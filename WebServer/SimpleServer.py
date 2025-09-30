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
            gc.collect()
            
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
                
                await asyncio.sleep_ms(50)  # Increased delay for better memory management
                
                # More aggressive garbage collection
                if gc.mem_free() < 15000:  # If less than 15KB free
                    gc.collect()
                
            except Exception as e:
                self.logger.error("SERVER: Loop error: " + str(e))
                await asyncio.sleep_ms(500)
                gc.collect()  # Collect on error
    
    async def handle_client(self, client, addr):
        self.logger.debug("SERVER: Client from " + str(addr))
        try:
            # Force garbage collection before handling request
            gc.collect()
            
            client.settimeout(1.0)
            
            try:
                request = client.recv(512).decode()  # Reduced buffer size
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
                    await self.handle_root_chunked(client)  # Use chunked response
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

    async def handle_root_chunked(self, client):
        """Send HTML response in chunks to avoid memory allocation errors"""
        try:
            # Send HTTP headers
            headers = "HTTP/1.1 200 OK\r\n"
            headers += "Content-Type: text/html\r\n"
            headers += "Connection: close\r\n"
            headers += "Cache-Control: no-cache\r\n\r\n"
            client.write(headers.encode())
            
            # Send HTML header
            await self._send_html_header(client)
            
            # Send status cards one by one
            await self._send_valve_card(client, 'hot_water_valve', 'Hot Water Valve')
            gc.collect()
            
            await self._send_valve_card(client, 'cold_water_valve', 'Cold Water Valve')
            gc.collect()
            
            await self._send_leak_card(client, 'zone_1', 'Leak Sensors (Zone 1)')
            gc.collect()
            
            await self._send_leak_card(client, 'zone_2', 'Leak Sensors (Zone 2)')
            gc.collect()
            
            await self._send_heater_card(client)
            gc.collect()
            
            await self._send_temperature_cards(client)
            gc.collect()
            
            await self._send_system_info(client)
            gc.collect()
            
            # Send HTML footer
            await self._send_html_footer(client)
            
        except Exception as e:
            self.logger.error("SERVER: Error sending chunked response: " + str(e))
    
    
    async def _send_html_header(self, client):
        """Send HTML header and basic page structure"""
        current_time = DsRTC().get_datetime_ddmmyy()
        
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
    </style>
</head>
<body>
    <h1>Water Control System</h1>
    <div class="version">Version """ + Settings.APP_VERSION + """</div>
    <p>Current time: """ + current_time + """</p>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
    
    async def _send_valve_card(self, client, valve_name, title):
        """Send a single valve card"""
        valve_state = self.states.get_valve_state(valve_name) or "unknown"
        valve_time = self.states.get_valve_action_time(valve_name)
        
        html = """<div class="card">
        <h2>""" + title + """</h2>
        <p>Valve State: <span class=\"""" + valve_state + """\">""" + valve_state + """</span></p>
        <p>State changed: """ + valve_time + """</p>
        <button onclick="fetch('/api/control?action=open_valve&device=""" + valve_name + """', {method: 'POST'}).then(() => location.reload())">Open</button>
        <button onclick="fetch('/api/control?action=close_valve&device=""" + valve_name + """', {method: 'POST'}).then(() => location.reload())">Close</button>
    </div>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
    
    async def _send_leak_card(self, client, zone_name, title):
        """Send a single leak sensor card"""
        leak_state = self.states.get_leak_sensor_state(zone_name) or "unknown"
        leak_time = self.states.get_leak_sensor_action_time(zone_name)
        
        html = """<div class="card">
        <h2>""" + title + """</h2>
        <p>Leak State: <span class=\"""" + leak_state + """\">""" + leak_state + """</span></p>
        <p>Last leak detected: """ + leak_time + """</p>
        <button onclick="fetch('/api/control?action=clear_alarm', {method: 'POST'}).then(() => location.reload())">Clear Alarm</button>
    </div>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
    
    async def _send_heater_card(self, client):
        """Send heater card"""
        heater_state = self.states.get_heater_state('heater_power_swith') or "Not installed"
        heater_time = self.states.get_heater_action_time('heater_power_swith')
        
        html = """<div class="card">
        <h2>Heater</h2>
        <p>Heater state: <span class=\"""" + heater_state + """\">""" + heater_state + """</span></p>
        <p>State changed: """ + heater_time + """</p>
        <button onclick="fetch('/api/control?action=toggle_heater&device=heater_power_swith', {method: 'POST'}).then(() => location.reload())">Toggle Power</button>
    </div>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
    
    async def _send_temperature_cards(self, client):
        """Send temperature cards"""
        # Hot water temperature
        hot_water_temp = self.states.get_temperature('hot_water_temp')
        temp_hot_time = self.states.get_temperature_action_time('hot_water_temp')
        
        hot_display = self._format_temp(hot_water_temp)
        
        html = """<div class="card">
        <h2>Hot Water line Temperature</h2>
        <p>Current temp: """ + hot_display + """</p>
        <p>State changed: """ + temp_hot_time + """</p>
    </div>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
        
        # Heater temperature
        heater_temp = self.states.get_temperature('heater_temp')
        temp_heater_time = self.states.get_temperature_action_time('heater_temp')
        
        heater_display = self._format_temp(heater_temp)
        
        html = """<div class="card">
        <h2>Heater Temperature</h2>
        <p>Current temp: """ + heater_display + """</p>
        <p>State changed: """ + temp_heater_time + """</p>
    </div>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
    
    def _format_temp(self, temp):
        """Format temperature for display"""
        if temp == "No temp sensor":
            return '<span style="color: red;">Sensor not found</span>'
        elif temp == "ERROR":
            return '<span style="color: red;">Sensor error</span>'
        elif temp is None:
            return '--'
        else:
            return str(temp) + " &deg;C"
    
    async def _send_system_info(self, client):
        """Send simplified system info"""
        mem_free = gc.mem_free() // 1024
        
        html = """<div class="card">
        <h2>System Information</h2>
        <p>Free Memory: """ + str(mem_free) + """ KB</p>
        <button onclick="if(confirm('Reboot device?')) fetch('/api/control?action=reboot', {method: 'POST'})">Reboot</button>
    </div>
"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)
    
    async def _send_html_footer(self, client):
        """Send HTML footer"""
        html = """<div class="footer">
        <p>&copy; 2025 Developer: Vlasiuk Dmitro (AdAvAn)</p>
        <p><a href="https://github.com/AdAvAn/WaterLeak">GitHub</a></p>
    </div>
    <script>
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>"""
        client.write(html.encode())
        await asyncio.sleep_ms(10)

    async def _reboot_device(self):
        self.logger.info("SERVER: Rebooting device by user request")
        await asyncio.sleep(1)
        import machine
        machine.reset()
        
    def handle_status(self, client):
        """Simplified status response"""
        gc.collect()  # Collect before creating response
        
        status = {
            "version": Settings.APP_VERSION,
            "date": DsRTC().get_datetime_iso8601(),
            "valves": {
                "hot": self.states.get_valve_state('hot_water_valve'),
                "cold": self.states.get_valve_state('cold_water_valve')
            },
            "leak": {
                "z1": self.states.get_leak_sensor_state('zone_1'),
                "z2": self.states.get_leak_sensor_state('zone_2')
            },
            "heater": self.states.get_heater_state('heater_power_swith'),
            "temp": {
                "hot": str(self.states.get_temperature('hot_water_temp')),
                "heater": str(self.states.get_temperature('heater_temp'))
            },
            "mem_free": gc.mem_free()
        }
        
        response = json.dumps(status)
        self.send_response(client, 200, "OK", response, "application/json")
        
    def handle_control(self, client, params):
        gc.collect()
        
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
                result = {"success": True, "message": "Toggled heater"}
                
            elif action == "clear_alarm":
                self.leak_sensors.clear()
                result = {"success": True, "message": "Alarm cleared"}

            elif action == "reboot":
                result = {"success": True, "message": "Rebooting..."}
                self.send_response(client, 200, "OK", json.dumps(result), "application/json")
                asyncio.create_task(self._reboot_device())
                return
            
            self.send_response(client, 200, "OK", json.dumps(result), "application/json")
        except Exception as e:
            self.logger.error("SERVER: Control error: " + str(e))
            error_response = json.dumps({"error": str(e)})
            self.send_response(client, 500, "Internal Server Error", error_response, "application/json")