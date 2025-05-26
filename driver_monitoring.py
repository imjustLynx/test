import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import random
import math
import json
from datetime import datetime
import folium
import webview
import requests
from geopy.distance import geodesic
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation

class DriverMonitoringSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Driver Monitoring & Emergency Response System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize pygame for sound alerts
        pygame.mixer.init()
        
        # Sound effects (you'll need to add these sound files)
        self.sounds = {
            'emergency_alert': None,  # Add: emergency_alert.wav
            'unconscious_detected': None,  # Add: unconscious_alert.wav
            'autonomous_engaged': None,  # Add: autonomous_mode.wav
            'v2v_alert': None,  # Add: v2v_communication.wav
            'heartbeat_warning': None  # Add: heart_warning.wav
        }
        
        # System state variables
        self.monitoring_active = False
        self.emergency_detected = False
        self.autonomous_mode = False
        self.driver_conscious = True
        self.heart_rate = 72
        self.fatigue_level = 0
        self.speed = 0
        self.current_location = [40.7128, -74.0060]  # NYC coordinates
        self.destination = [40.7589, -73.9851]  # Times Square
        self.emergency_contacts = ["Emergency Services", "Family Contact", "Medical Center"]
        
        # Camera and CV variables
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # V2V Communication simulation
        self.nearby_vehicles = [
            {"id": "VEH001", "distance": 50, "direction": "ahead"},
            {"id": "VEH002", "distance": 30, "direction": "behind"},
            {"id": "VEH003", "distance": 25, "direction": "left"},
        ]
        
        self.setup_gui()
        self.start_monitoring_thread()
        
    def setup_gui(self):
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Smart Driver Monitoring & Emergency Response System", 
                              font=('Arial', 16, 'bold'), fg='#00ff00', bg='#1a1a1a')
        title_label.pack(pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Configure notebook style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#2a2a2a')
        style.configure('TNotebook.Tab', background='#3a3a3a', foreground='white')
        
        # Create tabs
        self.create_monitoring_tab()
        self.create_emergency_tab()
        self.create_route_tab()
        self.create_v2v_tab()
        self.create_settings_tab()
        
    def create_monitoring_tab(self):
        # Driver Monitoring Tab
        monitor_frame = tk.Frame(self.notebook, bg='#2a2a2a')
        self.notebook.add(monitor_frame, text='Driver Monitoring')
        
        # Left panel - Camera feed
        left_panel = tk.Frame(monitor_frame, bg='#2a2a2a')
        left_panel.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(left_panel, text="Driver Camera Feed", font=('Arial', 12, 'bold'), 
                fg='white', bg='#2a2a2a').pack()
        
        self.camera_label = tk.Label(left_panel, bg='black')
        self.camera_label.pack(pady=10, fill='both', expand=True)
        
        # Camera controls
        cam_controls = tk.Frame(left_panel, bg='#2a2a2a')
        cam_controls.pack()
        
        self.start_cam_btn = tk.Button(cam_controls, text="Start Camera", 
                                      command=self.start_camera, bg='#4CAF50', fg='white')
        self.start_cam_btn.pack(side='left', padx=5)
        
        self.stop_cam_btn = tk.Button(cam_controls, text="Stop Camera", 
                                     command=self.stop_camera, bg='#f44336', fg='white')
        self.stop_cam_btn.pack(side='left', padx=5)
        
        # Right panel - Status and controls
        right_panel = tk.Frame(monitor_frame, bg='#2a2a2a')
        right_panel.pack(side='right', fill='y', padx=10, pady=10)
        
        # System status
        status_frame = tk.LabelFrame(right_panel, text="System Status", fg='white', bg='#2a2a2a')
        status_frame.pack(fill='x', pady=5)
        
        self.status_labels = {}
        status_items = [
            ("Monitoring Active", "monitoring_status"),
            ("Driver Conscious", "consciousness_status"),
            ("Emergency Detected", "emergency_status"),
            ("Autonomous Mode", "autonomous_status")
        ]
        
        for label, key in status_items:
            frame = tk.Frame(status_frame, bg='#2a2a2a')
            frame.pack(fill='x', pady=2)
            tk.Label(frame, text=f"{label}:", fg='white', bg='#2a2a2a').pack(side='left')
            self.status_labels[key] = tk.Label(frame, text="●", fg='red', bg='#2a2a2a')
            self.status_labels[key].pack(side='right')
        
        # Vital signs
        vitals_frame = tk.LabelFrame(right_panel, text="Vital Signs", fg='white', bg='#2a2a2a')
        vitals_frame.pack(fill='x', pady=5)
        
        self.heart_rate_label = tk.Label(vitals_frame, text="Heart Rate: 72 BPM", 
                                        fg='white', bg='#2a2a2a')
        self.heart_rate_label.pack()
        
        self.fatigue_label = tk.Label(vitals_frame, text="Fatigue Level: 0%", 
                                     fg='white', bg='#2a2a2a')
        self.fatigue_label.pack()
        
        # Controls
        controls_frame = tk.LabelFrame(right_panel, text="Emergency Simulation", 
                                      fg='white', bg='#2a2a2a')
        controls_frame.pack(fill='x', pady=5)
        
        tk.Button(controls_frame, text="Simulate Unconsciousness", 
                 command=self.simulate_unconsciousness, bg='#FF9800', fg='white').pack(pady=2)
        
        tk.Button(controls_frame, text="Simulate Heart Attack", 
                 command=self.simulate_heart_attack, bg='#f44336', fg='white').pack(pady=2)
        
        tk.Button(controls_frame, text="Simulate Fatigue", 
                 command=self.simulate_fatigue, bg='#FFC107', fg='black').pack(pady=2)
        
        tk.Button(controls_frame, text="Reset to Normal", 
                 command=self.reset_to_normal, bg='#4CAF50', fg='white').pack(pady=2)
        
    def create_emergency_tab(self):
        # Emergency Response Tab
        emergency_frame = tk.Frame(self.notebook, bg='#2a2a2a')
        self.notebook.add(emergency_frame, text='Emergency Response')
        
        # Emergency status
        status_frame = tk.LabelFrame(emergency_frame, text="Emergency Status", 
                                    fg='white', bg='#2a2a2a')
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.emergency_status_label = tk.Label(status_frame, text="No Emergency Detected", 
                                              font=('Arial', 14, 'bold'), fg='green', bg='#2a2a2a')
        self.emergency_status_label.pack(pady=10)
        
        # Emergency actions
        actions_frame = tk.LabelFrame(emergency_frame, text="Automated Actions", 
                                     fg='white', bg='#2a2a2a')
        actions_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.actions_text = tk.Text(actions_frame, bg='#1a1a1a', fg='white', 
                                   font=('Courier', 10))
        self.actions_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Emergency contacts
        contacts_frame = tk.LabelFrame(emergency_frame, text="Emergency Contacts", 
                                      fg='white', bg='#2a2a2a')
        contacts_frame.pack(fill='x', padx=10, pady=10)
        
        for contact in self.emergency_contacts:
            contact_frame = tk.Frame(contacts_frame, bg='#2a2a2a')
            contact_frame.pack(fill='x', pady=2)
            tk.Label(contact_frame, text=contact, fg='white', bg='#2a2a2a').pack(side='left')
            tk.Label(contact_frame, text="● Ready", fg='green', bg='#2a2a2a').pack(side='right')
        
    def create_route_tab(self):
        # Autonomous Route Tab
        route_frame = tk.Frame(self.notebook, bg='#2a2a2a')
        self.notebook.add(route_frame, text='Autonomous Routing')
        
        # Route information
        info_frame = tk.LabelFrame(route_frame, text="Route Information", 
                                  fg='white', bg='#2a2a2a')
        info_frame.pack(fill='x', padx=10, pady=10)
        
        self.route_info_text = tk.Text(info_frame, height=8, bg='#1a1a1a', fg='white')
        self.route_info_text.pack(fill='x', padx=5, pady=5)
        
        # Map placeholder (would integrate with folium/webview)
        map_frame = tk.LabelFrame(route_frame, text="Live Route Map", 
                                 fg='white', bg='#2a2a2a')
        map_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create matplotlib figure for route visualization
        self.fig, self.ax = plt.subplots(figsize=(8, 6), facecolor='#2a2a2a')
        self.ax.set_facecolor('#1a1a1a')
        self.canvas = FigureCanvasTkAgg(self.fig, map_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self.update_route_map()
        
        # Route controls
        controls_frame = tk.Frame(route_frame, bg='#2a2a2a')
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(controls_frame, text="Find Nearest Hospital", 
                 command=self.find_nearest_hospital, bg='#f44336', fg='white').pack(side='left', padx=5)
        
        tk.Button(controls_frame, text="Safe Stop Location", 
                 command=self.find_safe_stop, bg='#FF9800', fg='white').pack(side='left', padx=5)
        
        tk.Button(controls_frame, text="Continue to Destination", 
                 command=self.continue_route, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        
    def create_v2v_tab(self):
        # V2V Communication Tab
        v2v_frame = tk.Frame(self.notebook, bg='#2a2a2a')
        self.notebook.add(v2v_frame, text='V2V Communication')
        
        # Nearby vehicles
        vehicles_frame = tk.LabelFrame(v2v_frame, text="Nearby Vehicles", 
                                      fg='white', bg='#2a2a2a')
        vehicles_frame.pack(fill='x', padx=10, pady=10)
        
        # Create treeview for vehicles
        columns = ('ID', 'Distance', 'Direction', 'Status')
        self.vehicles_tree = ttk.Treeview(vehicles_frame, columns=columns, show='headings')
        
        for col in columns:
            self.vehicles_tree.heading(col, text=col)
            self.vehicles_tree.column(col, width=100)
        
        self.vehicles_tree.pack(fill='x', padx=5, pady=5)
        self.update_vehicles_list()
        
        # Communication log
        comm_frame = tk.LabelFrame(v2v_frame, text="Communication Log", 
                                  fg='white', bg='#2a2a2a')
        comm_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.comm_text = tk.Text(comm_frame, bg='#1a1a1a', fg='white', font=('Courier', 9))
        comm_scrollbar = tk.Scrollbar(comm_frame, command=self.comm_text.yview)
        self.comm_text.configure(yscrollcommand=comm_scrollbar.set)
        
        self.comm_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        comm_scrollbar.pack(side='right', fill='y')
        
        # V2V controls
        v2v_controls = tk.Frame(v2v_frame, bg='#2a2a2a')
        v2v_controls.pack(fill='x', padx=10, pady=5)
        
        tk.Button(v2v_controls, text="Broadcast Emergency Alert", 
                 command=self.broadcast_emergency, bg='#f44336', fg='white').pack(side='left', padx=5)
        
        tk.Button(v2v_controls, text="Request Safe Passage", 
                 command=self.request_safe_passage, bg='#FF9800', fg='white').pack(side='left', padx=5)
        
    def create_settings_tab(self):
        # Settings Tab
        settings_frame = tk.Frame(self.notebook, bg='#2a2a2a')
        self.notebook.add(settings_frame, text='Settings')
        
        # API Configuration
        api_frame = tk.LabelFrame(settings_frame, text="API Configuration", 
                                 fg='white', bg='#2a2a2a')
        api_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(api_frame, text="Google Maps API Key:", fg='white', bg='#2a2a2a').pack(anchor='w')
        self.api_key_entry = tk.Entry(api_frame, show='*', bg='#1a1a1a', fg='white', width=50)
        self.api_key_entry.pack(fill='x', padx=5, pady=5)
        
        # Emergency contacts
        contacts_frame = tk.LabelFrame(settings_frame, text="Emergency Contacts", 
                                      fg='white', bg='#2a2a2a')
        contacts_frame.pack(fill='x', padx=10, pady=10)
        
        self.contacts_listbox = tk.Listbox(contacts_frame, bg='#1a1a1a', fg='white', height=5)
        self.contacts_listbox.pack(fill='x', padx=5, pady=5)
        
        for contact in self.emergency_contacts:
            self.contacts_listbox.insert(tk.END, contact)
        
        # Vehicle settings
        vehicle_frame = tk.LabelFrame(settings_frame, text="Vehicle Settings", 
                                     fg='white', bg='#2a2a2a')
        vehicle_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(vehicle_frame, text="Maximum Speed (Autonomous):", 
                fg='white', bg='#2a2a2a').pack(anchor='w')
        self.max_speed_var = tk.StringVar(value="35")
        tk.Scale(vehicle_frame, from_=10, to=60, orient='horizontal', 
                variable=self.max_speed_var, bg='#2a2a2a', fg='white').pack(fill='x')
        
        # Save settings button
        tk.Button(settings_frame, text="Save Settings", command=self.save_settings, 
                 bg='#4CAF50', fg='white').pack(pady=10)
        
    def start_camera(self):
        try:
            if self.cap is not None:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(0)
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)  # Reduced FPS for better performance
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size
            
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                return
                
            self.monitoring_active = True
            self.camera_label.configure(text="Starting camera...", fg='white')
            self.root.after(100, self.update_camera_feed)  # Start after small delay
            
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {str(e)}")
    
    def stop_camera(self):
        self.monitoring_active = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.camera_label.configure(image='', bg='black')
    
    def update_camera_feed(self):
        if self.monitoring_active and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Get label dimensions for proper scaling
                label_width = self.camera_label.winfo_width()
                label_height = self.camera_label.winfo_height()
                
                # Set minimum size if label not yet rendered
                if label_width <= 1:
                    label_width = 480
                if label_height <= 1:
                    label_height = 360
                
                # Face detection (optimized)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Scale down for detection to improve performance
                small_gray = cv2.resize(gray, (320, 240))
                faces = self.face_cascade.detectMultiScale(small_gray, 1.2, 4, minSize=(30, 30))
                
                # Scale back face coordinates
                faces = [(int(x*2), int(y*2), int(w*2), int(h*2)) for (x, y, w, h) in faces]
                
                consciousness_detected = len(faces) > 0
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    roi_gray = gray[y:y+h, x:x+w]
                    
                    # Eye detection (less frequent for performance)
                    if hasattr(self, '_eye_detection_counter'):
                        self._eye_detection_counter += 1
                    else:
                        self._eye_detection_counter = 0
                    
                    # Only do eye detection every 5 frames
                    if self._eye_detection_counter % 5 == 0:
                        try:
                            eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(10, 10))
                            self._eyes_detected = len(eyes) >= 1
                        except:
                            self._eyes_detected = True
                    
                    if hasattr(self, '_eyes_detected') and self._eyes_detected:
                        cv2.putText(frame, "ALERT", (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, "DROWSY", (x, y-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        consciousness_detected = False
                
                self.driver_conscious = consciousness_detected
                
                # Convert to PhotoImage and display with proper scaling
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                
                # Scale to fit label while maintaining aspect ratio
                frame_width, frame_height = frame_pil.size
                aspect_ratio = frame_width / frame_height
                
                if label_width / label_height > aspect_ratio:
                    # Fit to height
                    new_height = label_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    # Fit to width
                    new_width = label_width
                    new_height = int(new_width / aspect_ratio)
                
                frame_pil = frame_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(frame_pil)
                
                self.camera_label.configure(image=photo, text="")
                self.camera_label.image = photo
            else:
                # If frame read fails, show error message
                self.camera_label.configure(image="", text="Camera Error", fg='red')
            
            # Reduced update frequency for better performance
            self.root.after(66, self.update_camera_feed)  # ~15 FPS
        else:
            self.camera_label.configure(image="", text="Camera Stopped", fg='white')
    
    def start_monitoring_thread(self):
        def monitor():
            while True:
                self.update_system_status()
                self.simulate_vitals()
                time.sleep(1)
        
        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()
    
    def update_system_status(self):
        # Update status indicators
        self.status_labels["monitoring_status"].configure(
            fg='green' if self.monitoring_active else 'red')
        self.status_labels["consciousness_status"].configure(
            fg='green' if self.driver_conscious else 'red')
        self.status_labels["emergency_status"].configure(
            fg='red' if self.emergency_detected else 'green')
        self.status_labels["autonomous_status"].configure(
            fg='green' if self.autonomous_mode else 'red')
        
        # Update vital signs
        self.heart_rate_label.configure(text=f"Heart Rate: {self.heart_rate} BPM")
        self.fatigue_label.configure(text=f"Fatigue Level: {self.fatigue_level}%")
        
        # Check for emergency conditions
        if not self.driver_conscious or self.heart_rate > 120 or self.heart_rate < 50:
            if not self.emergency_detected:
                self.trigger_emergency()
    
    def simulate_vitals(self):
        if not self.emergency_detected:
            # Normal variation
            self.heart_rate += random.randint(-2, 2)
            self.heart_rate = max(60, min(100, self.heart_rate))
            self.fatigue_level += random.randint(-1, 1)
            self.fatigue_level = max(0, min(30, self.fatigue_level))
    
    def simulate_unconsciousness(self):
        self.driver_conscious = False
        self.log_action("SIMULATION: Driver unconsciousness detected")
    
    def simulate_heart_attack(self):
        self.heart_rate = random.randint(140, 180)
        self.log_action("SIMULATION: Abnormal heart rate detected - possible cardiac event")
    
    def simulate_fatigue(self):
        self.fatigue_level = random.randint(70, 95)
        self.log_action("SIMULATION: High fatigue level detected")
    
    def reset_to_normal(self):
        self.driver_conscious = True
        self.emergency_detected = False
        self.autonomous_mode = False
        self.heart_rate = 72
        self.fatigue_level = 10
        self.emergency_status_label.configure(text="No Emergency Detected", fg='green')
        self.log_action("System reset to normal operation")
    
    def trigger_emergency(self):
        self.emergency_detected = True
        self.autonomous_mode = True
        self.emergency_status_label.configure(text="EMERGENCY DETECTED - AUTONOMOUS MODE ACTIVE", 
                                            fg='red')
        
        self.log_action("🚨 EMERGENCY DETECTED!")
        self.log_action("→ Engaging autonomous driving mode")
        self.log_action("→ Reducing speed to safe level")
        self.log_action("→ Broadcasting V2V emergency alert")
        self.log_action("→ Calculating route to nearest hospital")
        self.log_action("→ Notifying emergency contacts")
        
        # Trigger V2V alert
        self.broadcast_emergency()
        
        # Find nearest hospital
        self.find_nearest_hospital()
    
    def log_action(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.actions_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.actions_text.see(tk.END)
    
    def log_communication(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.comm_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.comm_text.see(tk.END)
    
    def update_vehicles_list(self):
        # Clear existing items
        for item in self.vehicles_tree.get_children():
            self.vehicles_tree.delete(item)
        
        # Add vehicles
        for vehicle in self.nearby_vehicles:
            status = "Alerted" if self.emergency_detected else "Normal"
            self.vehicles_tree.insert('', 'end', values=(
                vehicle['id'], f"{vehicle['distance']}m", 
                vehicle['direction'], status))
    
    def broadcast_emergency(self):
        self.log_communication("🚨 BROADCASTING EMERGENCY ALERT TO NEARBY VEHICLES")
        for vehicle in self.nearby_vehicles:
            self.log_communication(f"→ Alert sent to {vehicle['id']} ({vehicle['distance']}m {vehicle['direction']})")
        self.update_vehicles_list()
    
    def request_safe_passage(self):
        self.log_communication("📡 Requesting safe passage from nearby vehicles")
        self.log_communication("→ Asking vehicles to maintain safe distance")
        self.log_communication("→ Requesting clear emergency lane")
    
    def update_route_map(self):
        self.ax.clear()
        self.ax.set_facecolor('#1a1a1a')
        
        # Current location
        current_x, current_y = 0, 0
        self.ax.scatter(current_x, current_y, c='blue', s=100, label='Current Location', marker='o')
        
        # Destination
        dest_x, dest_y = 5, 3
        self.ax.scatter(dest_x, dest_y, c='green', s=100, label='Destination', marker='s')
        
        # Route
        route_x = [0, 1, 2, 3, 4, 5]
        route_y = [0, 0.5, 1, 1.5, 2.5, 3]
        self.ax.plot(route_x, route_y, 'g--', alpha=0.7, label='Original Route')
        
        if self.emergency_detected:
            # Emergency route to hospital
            hospital_x, hospital_y = 2, 4
            self.ax.scatter(hospital_x, hospital_y, c='red', s=100, label='Hospital', marker='+')
            
            emergency_route_x = [0, 1, 2]
            emergency_route_y = [0, 2, 4]
            self.ax.plot(emergency_route_x, emergency_route_y, 'r-', linewidth=3, 
                        label='Emergency Route')
        
        self.ax.set_xlim(-1, 6)
        self.ax.set_ylim(-1, 5)
        self.ax.set_xlabel('Longitude (relative)', color='white')
        self.ax.set_ylabel('Latitude (relative)', color='white')
        self.ax.tick_params(colors='white')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def find_nearest_hospital(self):
        self.log_action("🏥 Calculating route to nearest hospital...")
        self.log_action("→ Found: City General Hospital (2.3 km)")
        self.log_action("→ ETA: 4 minutes (autonomous mode)")
        self.update_route_map()
        
        # Update route info
        route_info = """
EMERGENCY ROUTE TO HOSPITAL

Current Location: Downtown Area
Destination: City General Hospital
Distance: 2.3 km
Estimated Time: 4 minutes
Route Status: Active - Autonomous Mode

Emergency Services Notified: YES
Expected Response Time: 3 minutes

Vehicle Status:
- Speed: Reduced to 25 mph
- Hazard lights: ON
- Emergency beacon: ACTIVE
        """
        self.route_info_text.delete(1.0, tk.END)
        self.route_info_text.insert(1.0, route_info.strip())
    
    def find_safe_stop(self):
        self.log_action("🛑 Finding safe stop location...")
        self.log_action("→ Located: Emergency Pull-off Area (300m ahead)")
        self.log_action("→ Initiating controlled stop sequence")
    
    def continue_route(self):
        if not self.emergency_detected:
            self.log_action("📍 Continuing to original destination")
            self.update_route_map()
    
    def save_settings(self):
        messagebox.showinfo("Settings", "Settings saved successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DriverMonitoringSystem(root)
    root.mainloop()