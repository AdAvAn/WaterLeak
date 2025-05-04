import socket
import json
import gc
import uasyncio as asyncio
from RTC.DsRTC import DsRTC


class SimpleServer:
    def __init__(self, states, display, valves, leak_sensors, heater_switch):
        from Logging.AppLogger import AppLogger
        from Helpers.WiFiManager import WiFiManager
        self.logger = AppLogger()
        self.states = states
        self.display = display
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
            
            self.logger.info(f"SERVER: Started on http://{self.wifi_manager.get_ip_address()}/")
            return True
        except Exception as e:
            self.logger.error(f"SERVER: Start error: {e}")
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
                self.logger.error(f"SERVER: Loop error: {e}")
                await asyncio.sleep_ms(500)
    
    async def handle_client(self, client, addr):
        self.logger.debug(f"SERVER: Client from {addr}")
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
                self.logger.error(f"SERVER: Request error: {e}")
                self.send_response(client, 400, "Bad Request", str(e))
        except Exception as e:
            self.logger.error(f"SERVER: Client error: {e}")
        finally:
            client.close()
            gc.collect()
    
    def send_response(self, client, status_code, status_text, content, content_type="text/html"):
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += "Connection: close\r\n"
        
        content_bytes = content.encode() if isinstance(content, str) else content
        response += f"Content-Length: {len(content_bytes)}\r\n\r\n"
        
        client.write(response.encode())
        client.write(content_bytes)
    
    def handle_root(self, client):
        # Getting temperature data
        hot_water_temp = self.states.get_temperature('hot_water_temp')
        hot_water_prev = self.states.get_temperature_preview_state('hot_water_temp')
        heater_temp = self.states.get_temperature('heater_temp')
        heater_prev = self.states.get_temperature_preview_state('heater_temp')
        
        # Function for determining the trend
        def get_trend(current, prev):
            if current is None or prev is None:
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
        
        # Identify trends to display
        hot_water_trend = get_trend(hot_water_temp, hot_water_prev)
        heater_trend = get_trend(heater_temp, heater_prev)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Water Control</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial; margin: 0; padding: 20px; }}
                h1 {{ color: #0066cc; }}
                .card {{ background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .leak {{ color: red; font-weight: bold; }}
                .no_leak {{ color: green; }}
                .opened, .On {{ color: green; font-weight: bold; }}
                .closed, .Off {{ color: red; font-weight: bold; }}
                button {{ padding: 5px 10px; margin: 5px; cursor: pointer; }}
                .trend-up {{ color: red; }}
                .trend-down {{ color: blue; }}
                .trend-same {{ color: gray; }}
            </style>
        </head>
        <body>
            <h1>Water Control System</h1>
            <p>Current time: {DsRTC().get_datetime_ddmmyy()}</p>
            
            <div class="card">
                <h2>Hot Water Valve</h2>
                <p>State: <span class="{self.states.get_valve_state('hot_water_valve')}">{self.states.get_valve_state('hot_water_valve')}</span></p>
                <button onclick="fetch('/api/control?action=open_valve&device=hot_water_valve', {{method: 'POST'}}).then(() => location.reload())">Open</button>
                <button onclick="fetch('/api/control?action=close_valve&device=hot_water_valve', {{method: 'POST'}}).then(() => location.reload())">Close</button>
            </div>
            
            <div class="card">
                <h2>Cold Water Valve</h2>
                <p>State: <span class="{self.states.get_valve_state('cold_water_valve')}">{self.states.get_valve_state('cold_water_valve')}</span></p>
                <button onclick="fetch('/api/control?action=open_valve&device=cold_water_valve', {{method: 'POST'}}).then(() => location.reload())">Open</button>
                <button onclick="fetch('/api/control?action=close_valve&device=cold_water_valve', {{method: 'POST'}}).then(() => location.reload())">Close</button>
            </div>
            
            <div class="card">
                <h2>Leak Sensors</h2>
                <p>Zone 1: <span class="{self.states.get_leak_sensor_state('zone_1')}">{self.states.get_leak_sensor_state('zone_1')}</span></p>
                <p>Zone 2: <span class="{self.states.get_leak_sensor_state('zone_2')}">{self.states.get_leak_sensor_state('zone_2')}</span></p>
                <button onclick="fetch('/api/control?action=clear_alarm', {{method: 'POST'}}).then(() => location.reload())">Clear Alarm</button>
            </div>
            
            <div class="card">
                <h2>Heater</h2>
                <p>State: <span class="{self.states.get_heater_state('heater_power_swith')}">{self.states.get_heater_state('heater_power_swith')}</span></p>
                <button onclick="fetch('/api/control?action=toggle_heater&device=heater_power_swith', {{method: 'POST'}}).then(() => location.reload())">Toggle Power</button>
            </div>
            
            <div class="card">
                <h2>Temperatures</h2>
                <p>Hot Water: {hot_water_temp or '--'} &deg;C <span class="trend-{'up' if hot_water_trend == '↑' else 'down' if hot_water_trend == '↓' else 'same'}">{hot_water_trend}</span></p>
                <p>Heater: {heater_temp or '--'} &deg;C <span class="trend-{'up' if heater_trend == '↑' else 'down' if heater_trend == '↓' else 'same'}">{heater_trend}</span></p>
            </div>
            
            <script>
                setTimeout(() => location.reload(), 5000);
            </script>
        </body>
        </html>
        """
        self.send_response(client, 200, "OK", html)

    def handle_status(self, client):
        status = {
            "date": self.states._ds_rtc.get_datetime_iso8601(),
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
                "hot_water": self.states.get_temperature('hot_water_temp'),
                "heater": self.states.get_temperature('heater_temp')
            }
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
                result = {"success": True, "message": f"Opening {device}"}
                
            elif action == "close_valve" and device in ["hot_water_valve", "cold_water_valve"]:
                valve = self.valves.hot_water_valve if device == "hot_water_valve" else self.valves.cold_water_valve
                valve.close()
                result = {"success": True, "message": f"Closing {device}"}
                
            elif action == "toggle_heater" and device == "heater_power_swith" and self.heater_switch:
                self.heater_switch.toggle()
                result = {"success": True, "message": "Toggled heater power"}
                
            elif action == "clear_alarm":
                self.display.reset_alarm()
                result = {"success": True, "message": "Alarm cleared"}
            
            self.send_response(client, 200, "OK", json.dumps(result), "application/json")
        except Exception as e:
            self.logger.error(f"SERVER: Control error: {e}")
            self.send_response(client, 500, "Internal Server Error", json.dumps({"error": str(e)}), "application/json")