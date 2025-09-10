import socket
import json
import gc
import uasyncio as asyncio
from RTC.DsRTC import DsRTC
import Resources.Settings as Settings

class SimpleServer:
    def __init__(self, states, valves, leak_sensors, heater_switch):
        from Logging.AppLogger import AppLogger
        from Helpers.WiFiManager import WiFiManager
        self.logger = AppLogger()
        self.states = states
        self.valves = valves
        self.leak_sensors = leak_sensors
        self.heater_switch = heater_switch
        
        self.wifi_manager = WiFiManager()
        self.server_socket = None
    
    def start(self):
        if not self.wifi_manager.is_wifi_connected():
            self.logger.error("SERVER: WiFi not connected")
            return False
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.setblocking(False)
            
            addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
            self.server_socket.bind(addr)
            self.server_socket.listen(5)
            
            ip_addr = self.wifi_manager.get_ip_address()
            self.logger.info("SERVER: Started on http://" + str(ip_addr) + "/")
            return True
        except Exception as e:
            self.logger.error("SERVER: Start error: " + str(e))
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None
            return False
    
    async def run(self):
        if not self.server_socket:
            self.logger.error("SERVER: Socket not initialized")
            return
            
        self.logger.info("SERVER: Loop starting")
        
        while True:
            try:
                try:
                    client, addr = self.server_socket.accept()
                    asyncio.create_task(self.handle_client(client, addr))
                except OSError:
                    # Normal behavior for a non-blocking socket
                    pass
                
                await asyncio.sleep_ms(20)
                gc.collect()
                
            except Exception as e:
                self.logger.error("SERVER: Loop error: " + str(e))
                await asyncio.sleep_ms(500)
    
    async def handle_client(self, client, addr):
        self.logger.debug("SERVER: Client from " + str(addr))
        try:
            client.settimeout(1.0)
            
            try:
                request = client.recv(1024).decode()
                request_line = request.split('\r\n')[0]
                method, path, _ = request_line.split(' ')
                
                # Processing request parameters
                params = {}
                if '?' in path:
                    path, query = path.split('?')
                    for param in query.split('&'):
                        if '=' in param:
                            key, value = param.split('=')
                            params[key] = value
                
                # Request Routing
                if path == '/':
                    self.handle_root(client)
                elif path == '/api/status':
                    self.handle_status(client)
                elif path == '/api/control' and method == 'POST':
                    self.handle_control(client, params)
                else:
                    self.send_response(client, 404, "Not Found", "Page not found")
            except Exception as e:
                self.logger.error("SERVER: Request error: " + str(e))
                self.send_response(client, 400, "Bad Request", str(e))
        except Exception as e:
            self.logger.error("SERVER: Client error: " + str(e))
        finally:
            client.close()
            gc.collect()
    
    def send_response(self, client, status_code, status_text, content, content_type="text/html"):
        response = "HTTP/1.1 " + str(status_code) + " " + status_text + "\r\n"
        response += "Content-Type: " + content_type + "\r\n"
        response += "Connection: close\r\n"
        
        content_bytes = content.encode() if isinstance(content, str) else content
        response += "Content-Length: " + str(len(content_bytes)) + "\r\n\r\n"
        
        client.write(response.encode())
        client.write(content_bytes)

    async def _reboot_device(self):
        self.logger.info("SERVER: Rebooting device by user request")
        await asyncio.sleep(1)  # Allow response to be sent before reboot
        import machine
        machine.reset()
    
    def handle_root(self, client):
        # Getting temperature data
        hot_water_temp = self.states.get_temperature('hot_water_temp')
        hot_water_prev = self.states.get_temperature_preview_state('hot_water_temp')
        heater_temp = self.states.get_temperature('heater_temp')
        heater_prev = self.states.get_temperature_preview_state('heater_temp')
        
        # Function for determining the trend
        def get_trend(current, prev):
            # Handle error states
            if current in ["No temp sensor", "ERROR", None] or prev in ["No temp sensor", "ERROR", None]:
                return ""
            if isinstance(current, str) or isinstance(prev, str):
                return ""
            try:
                if float(current) > float(prev):
                    return "↑" 
                elif float(current) < float(prev):
                    return "↓" 
                else:
                    return "→" 
            except:
                return ""
        
        # Function to format temperature display
        def format_temp_display(temp, trend):
            if temp == "No temp sensor":
                return "Sensor not found", "red"
            elif temp == "ERROR":
                return "Sensor error", "red"
            elif temp is None:
                return "--", "gray"
            else:
                temp_str = str(temp) + " &deg;C"
                if trend:
                    trend_class = "up" if trend == "↑" else "down" if trend == "↓" else "same"
                    temp_str += " <span class=\"trend-" + trend_class + "\">" + trend + "</span>"
                return temp_str, ""
        
        # Identify trends to display
        hot_water_trend = get_trend(hot_water_temp, hot_water_prev)
        heater_trend = get_trend(heater_temp, heater_prev)
        
        # Format temperature displays
        hot_water_display, hot_water_color = format_temp_display(hot_water_temp, hot_water_trend)
        heater_display, heater_color = format_temp_display(heater_temp, heater_trend)
        
        # Get system information
        system_info = self.get_system_info()
        
        # Get valve states
        hot_valve_state = self.states.get_valve_state('hot_water_valve') or "unknown"
        cold_valve_state = self.states.get_valve_state('cold_water_valve') or "unknown"
        leak_zone1 = self.states.get_leak_sensor_state('zone_1') or "unknown"
        leak_zone2 = self.states.get_leak_sensor_state('zone_2') or "unknown"
        heater_state = self.states.get_heater_state('heater_power_swith') or "Not installed"
        
        # Get action times
        hot_valve_time = self.states.get_valve_action_time('hot_water_valve')
        cold_valve_time = self.states.get_valve_action_time('cold_water_valve')
        leak1_time = self.states.get_leak_sensor_action_time('zone_1')
        leak2_time = self.states.get_leak_sensor_action_time('zone_2')
        heater_time = self.states.get_heater_action_time('heater_power_swith')
        temp_hot_time = self.states.get_temperature_action_time('hot_water_temp')
        temp_heater_time = self.states.get_temperature_action_time('heater_temp')
        
        # Get current time
        current_time = DsRTC().get_datetime_ddmmyy()
        
        # Memory info
        mem_used_kb = system_info["memory"]["used"] // 1024
        mem_free_kb = system_info["memory"]["free"] // 1024
        mem_percent = system_info["memory"]["percent_used"]
        
        # CPU temp
        cpu_temp = system_info["cpu_temp"]
        
        # Storage info
        if isinstance(system_info["filesystem"]["used"], str):
            storage_used_kb = "N/A"
            storage_free_kb = "N/A" 
            storage_percent = 0
        else:
            storage_used_kb = system_info["filesystem"]["used"] // 1024
            storage_free_kb = system_info["filesystem"]["free"] // 1024
            storage_percent = system_info["filesystem"]["percent_used"]
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Water Control v.""" + Settings.APP_VERSION + """</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; }
        h1 { color: #0066cc; }
        .version { color: #666; font-size: 14px; margin-bottom: 20px; }
        .card { background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .leak { color: red; font-weight: bold; }
        .no_leak { color: green; }
        .opened, .On { color: green; font-weight: bold; }
        .closed, .Off { color: red; font-weight: bold; }
        button { padding: 5px 10px; margin: 5px; cursor: pointer; }
        .trend-up { color: red; }
        .trend-down { color: blue; }
        .trend-same { color: gray; }
        .sensor-error { color: red; font-weight: bold; }
        .progress-bar { 
            height: 20px; 
            background-color: #e0e0e0; 
            border-radius: 5px; 
            margin-top: 5px; 
        }
        .progress { 
            height: 100%; 
            background-color: #4CAF50; 
            border-radius: 5px; 
            text-align: center; 
            line-height: 20px; 
            color: white; 
        }
        .system-info { display: flex; flex-wrap: wrap; gap: 10px; }
        .system-box { flex: 1; min-width: 150px; }
        .footer {
            margin-top: 30px;
            padding: 20px 0;
            border-top: 1px solid #ccc;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        .footer a {
            color: #0066cc;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>Water Control System</h1>
    <div class="version">Version """ +Settings.APP_VERSION + """</div>
    <p>Current time: """ + current_time + """</p>
    
    <div class="card">
        <h2>Hot Water Valve</h2>
        <p>Valve State: <span class=\"""" + hot_valve_state + """\">""" + hot_valve_state + """</span></p>
        <p>State changed: """ + hot_valve_time + """</p>
        <button onclick="fetch('/api/control?action=open_valve&device=hot_water_valve', {method: 'POST'}).then(() => location.reload())">Open</button>
        <button onclick="fetch('/api/control?action=close_valve&device=hot_water_valve', {method: 'POST'}).then(() => location.reload())">Close</button>
    </div>
    
    <div class="card">
        <h2>Cold Water Valve</h2>
        <p>Valve State: <span class=\"""" + cold_valve_state + """\">""" + cold_valve_state + """</span></p>
        <p>State changed: """ + cold_valve_time + """</p>
        <button onclick="fetch('/api/control?action=open_valve&device=cold_water_valve', {method: 'POST'}).then(() => location.reload())">Open</button>
        <button onclick="fetch('/api/control?action=close_valve&device=cold_water_valve', {method: 'POST'}).then(() => location.reload())">Close</button>
    </div>
    
    <div class="card">
        <h2>Leak Sensors (Zone 1)</h2>
        <p>Leak State: <span class=\"""" + leak_zone1 + """\">""" + leak_zone1 + """</span></p>
        <p>Last leak detected: """ + leak1_time + """</p>
        <button onclick="fetch('/api/control?action=clear_alarm', {method: 'POST'}).then(() => location.reload())">Clear Alarm</button>
    </div>

    <div class="card">
        <h2>Leak Sensors (Zone 2)</h2>
        <p>Leak State: <span class=\"""" + leak_zone2 + """\">""" + leak_zone2 + """</span></p>
        <p>Last leak detected: """ + leak2_time + """</p>
        <button onclick="fetch('/api/control?action=clear_alarm', {method: 'POST'}).then(() => location.reload())">Clear Alarm</button>
    </div>
    
    <div class="card">
        <h2>Heater</h2>
        <p>Heater state: <span class=\"""" + heater_state + """\">""" + heater_state + """</span></p>
        <p>State changed: """ + heater_time + """</p>
        <button onclick="fetch('/api/control?action=toggle_heater&device=heater_power_swith', {method: 'POST'}).then(() => location.reload())">Toggle Power</button>
    </div>
    
    <div class="card">
        <h2>Hot Water line Temperature</h2>"""

        if hot_water_color:
            html += """<p style="color: """ + hot_water_color + """;">Current temp: """ + hot_water_display + """</p>"""
        else:
            html += """<p>Current temp: """ + hot_water_display + """</p>"""
            
        html += """<p>State changed: """ + temp_hot_time + """</p>
    </div>
    
    <div class="card">
        <h2>Heater Temperature</h2>"""
        
        if heater_color:
            html += """<p style="color: """ + heater_color + """;">Current temp: """ + heater_display + """</p>"""
        else:
            html += """<p>Current temp: """ + heater_display + """</p>"""
            
        html += """<p>State changed: """ + temp_heater_time + """</p>
    </div>

    <div class="card">
        <h2>System Information</h2>
        <div class="system-info">
            <div class="system-box">
                <h3>Memory</h3>
                <p>Used: """ + str(mem_used_kb) + """ KB</p>
                <p>Free: """ + str(mem_free_kb) + """ KB</p>
                <div class="progress-bar">
                    <div class="progress" style="width: """ + str(mem_percent) + """%">
                        """ + str(mem_percent) + """%
                    </div>
                </div>
            </div>
            
            <div class="system-box">
                <h3>CPU</h3>
                <p>Temperature: """ + str(cpu_temp) + """ &deg;C</p>
            </div>
            
            <div class="system-box">
                <h3>Storage</h3>
                <p>Used: """ + str(storage_used_kb) + """ KB</p>
                <p>Free: """ + str(storage_free_kb) + """ KB</p>
                <div class="progress-bar">
                    <div class="progress" style="width: """ + str(storage_percent) + """%">
                        """ + str(storage_percent) + """%
                    </div>
                </div>
            </div>
            <div class="system-box">
                <h3>Reboot</h3>
                <div style="text-align: center;">
                    <button onclick="if(confirm('Are you sure you want to reboot the device?')) fetch('/api/control?action=reboot', {method: 'POST'}).then(() => alert('Device is rebooting...'));">Reboot Device</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>&copy; 2025 Developer: Vlasiuk Dmitro (AdAvAn)</p>
        <p>Source code: <a href="https://github.com/AdAvAn/WaterLeak" target="_blank">https://github.com/AdAvAn/WaterLeak</a></p>
    </div>
    
    <script>
        setTimeout(() => location.reload(), 5000);
    </script>
</body>
</html>"""
        
        self.send_response(client, 200, "OK", html)

    def handle_status(self, client):
        # Get temperature data with error handling
        hot_water_temp = self.states.get_temperature('hot_water_temp')
        heater_temp = self.states.get_temperature('heater_temp')
        
        # Convert error states to readable format for API
        if hot_water_temp == "No temp sensor":
            hot_water_temp = "sensor_not_found"
        elif hot_water_temp == "ERROR":
            hot_water_temp = "sensor_error"
            
        if heater_temp == "No temp sensor":
            heater_temp = "sensor_not_found"
        elif heater_temp == "ERROR":
            heater_temp = "sensor_error"
        
        status = {
            "version": Settings.APP_VERSION,
            "date": DsRTC().get_datetime_iso8601(),
            "valves": {
                "hot_water_valve": self.states.get_valve_state('hot_water_valve'),
                "cold_water_valve": self.states.get_valve_state('cold_water_valve')
            },
            "leak": {
                "zone_1": self.states.get_leak_sensor_state('zone_1'),
                "zone_2": self.states.get_leak_sensor_state('zone_2')
            },
            "heater": self.states.get_heater_state('heater_power_swith'),
            "temperature": {
                "hot_water": hot_water_temp,
                "heater": heater_temp
            },
            "system": self.get_system_info()
        }
        self.send_response(client, 200, "OK", json.dumps(status), "application/json")
        
    def handle_control(self, client, params):
        action = params.get('action')
        device = params.get('device')
        result = {"success": False, "message": "Unknown action"}
        
        try:
            if action == "open_valve" and device in ["hot_water_valve", "cold_water_valve"]:
                valve = self.valves.hot_water_valve if device == "hot_water_valve" else self.valves.cold_water_valve
                valve.open()
                result = {"success": True, "message": "Opening " + device}
                
            elif action == "close_valve" and device in ["hot_water_valve", "cold_water_valve"]:
                valve = self.valves.hot_water_valve if device == "hot_water_valve" else self.valves.cold_water_valve
                valve.close()
                result = {"success": True, "message": "Closing " + device}
                
            elif action == "toggle_heater" and device == "heater_power_swith" and self.heater_switch:
                self.heater_switch.toggle()
                result = {"success": True, "message": "Toggled heater power"}
                
            elif action == "clear_alarm":
                self.leak_sensors.clear()
                result = {"success": True, "message": "Alarm cleared"}

            elif action == "reboot":
                result = {"success": True, "message": "Rebooting device..."}
                self.send_response(client, 200, "OK", json.dumps(result), "application/json")
                asyncio.create_task(self._reboot_device())
                return
            
            self.send_response(client, 200, "OK", json.dumps(result), "application/json")
        except Exception as e:
            self.logger.error("SERVER: Control error: " + str(e))
            self.send_response(client, 500, "Internal Server Error", json.dumps({"error": str(e)}), "application/json")
            
    def get_system_info(self):
        import gc
        import machine
        import os
        
        # Get memory info
        mem_free = gc.mem_free()
        mem_alloc = gc.mem_alloc()
        total_mem = mem_free + mem_alloc
        
        # Get CPU temperature (only available on Pico)
        try:
            cpu_temp = machine.ADC(4).read_u16() * 3.3 / 65535
            # Convert to celsius
            cpu_temp = 27 - (cpu_temp - 0.706) / 0.001721
            cpu_temp = round(cpu_temp, 1)
        except:
            cpu_temp = "N/A"
        
        # Get filesystem info
        try:
            fs_stat = os.statvfs('/')
            fs_size = fs_stat[0] * fs_stat[2]  # block size * total blocks
            fs_free = fs_stat[0] * fs_stat[3]  # block size * free blocks
            fs_used = fs_size - fs_free
            fs_percent = round((fs_used / fs_size) * 100, 1)
        except:
            fs_size = fs_free = fs_used = fs_percent = "N/A"
        
        return {
            "memory": {
                "free": mem_free,
                "used": mem_alloc,
                "total": total_mem,
                "percent_used": round((mem_alloc / total_mem) * 100, 1)
            },
            "cpu_temp": cpu_temp,
            "filesystem": {
                "total": fs_size,
                "free": fs_free,
                "used": fs_used,
                "percent_used": fs_percent
            }
        }