#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
import tkinter.simpledialog as simpledialog
import tkinter.ttk as ttk
from PIL import Image, ImageTk, ImageEnhance

import requests
import json
import base64
from glob import glob
from dotenv import dotenv_values

import zmq
import io

class ImageProperties():
    def __init__(self):
        self.config = dotenv_values('.env')
        self.url = f"http://{self.config['SVC_URL']}:{self.config['FLASK_RUN_PORT']}/{self.config['API_ENDPOINT']}"
        self.image_width = 0
        self.image_height = 0
        self.image_format = ""
        self.image_color_mode = ""
        self.image_size = 0


    def extract_data(self, file):
        with open(file, 'rb') as img:
            base64_img_string = base64.b64encode(img.read()).decode('UTF-8')

            req_data = {
                "image" : base64_img_string
            }
            
            try:                
                resp = requests.post(self.url, json=req_data)
                img_data = json.loads(resp.text)
                self.image_width = img_data['width']
                self.image_height = img_data['heigth']
                self.image_format = img_data['format']
                self.image_color_mode = img_data['color_mode']
                self.image_size = img_data['file_size']

                return img_data
            
            except Exception as exc:
                print(f"Unexpected Exception: {exc}")
                return None

class ImageViewer():
    def __init__(self):
        #initialize GUI window
        self.window = tk.Tk()
        self.window.title("Mikeys Image Editor")
        self.window.geometry("1280x720")

        #set min/max window size
        self.window.minsize(800, 600)
        self.window.maxsize(1400, 1050)

        self.window.resizable(True, True)

        #create menu bar
        self.menubar = tk.Menu(self.window, relief='flat', border=0)
        self.window.config(menu=self.menubar)

        #create file menu with border
        self.file_menu = tk.Menu(
            self.menubar, 
            tearoff=0,
            relief='solid',
            border=1,
            activeborderwidth=1
        )

        #add a cascade menu
        self.menubar.add_cascade(
            label="File", 
            menu=self.file_menu,
            underline=-1
        )
        
        #create filter menu with border
        self.filter_menu = tk.Menu(
            self.menubar,
            tearoff=0,
            relief='solid',
            border=1,
            activeborderwidth=1
        )
        
        #add filter cascade menu
        self.menubar.add_cascade(
            label="Filter",
            menu=self.filter_menu,
            underline=-1
        )
        
        #add filter menu items
        self.filter_menu.add_command(label="Grayscale", command=self.apply_grayscale)
        self.filter_menu.add_separator()
        self.filter_menu.add_command(label="Remove Filters", command=self.remove_filters)

        #add the menu items
        self.file_menu.add_command(label="Upload", command=self.upload_image)
        self.file_menu.add_command(label="Save", command=self.save_image)
        self.file_menu.add_command(label="Save As", command=self.save_image_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.confirm_exit)

        self.window.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        #configure window grid weights to make it responsive
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Add weight to column 1 for the properties panel
        self.window.grid_columnconfigure(1, weight=0)  # No weight so it doesn't resize

        #create image frame with defined minimum size
        self.main_frame = tk.Frame(self.window, bg='white', width=1067, height=600)
        self.main_frame.grid(row=1, column=0, padx=(20, 10), pady=20, sticky='nsew')
        #prevent the frame from shrinking below minimum size
        self.main_frame.grid_propagate(False)

        #configure frame weights for internal resizing
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        #create label for frame
        self.image_label = tk.Label(self.main_frame, bg='white')
        self.image_label.grid(row=0, column=0, sticky='nsew')

        #add text instruction
        self.instruction = tk.Label(self.main_frame,
            text="Click On This Window To Select An Image\nSupported File Types: .png, .jpg, .jpeg",
            justify='center',
            anchor='center',
            bg='white')
        self.instruction.grid(row=0, column=0, sticky='nsew')

        # Create properties panel frame
        self.properties_frame = tk.Frame(
            self.window,
            bg='white',
            relief='solid',
            border=1,
            width=250,
            height=600
        )
        self.properties_frame.grid(row=1, column=1, padx=(0, 20), pady=20, sticky='nse')
        self.properties_frame.grid_propagate(False)

        # Add title to properties panel
        self.properties_title = tk.Label(
            self.properties_frame,
            text="Image Properties",
            font=('Arial', 12, 'bold'),
            bg='white',
            anchor='center'
        )
        self.properties_title.grid(row=0, column=0, padx=5, pady=10, sticky='ew')

        # Add properties labels
        self.prop_labels = {}
        properties = [
            "Width:", "Height:", "Format:", "Color Mode:", "File Size:"
        ]
        
        # Create labels for property names
        for i, prop in enumerate(properties):
            label = tk.Label(
                self.properties_frame,
                text=prop,
                font=('Arial', 10, 'bold'),
                bg='white',
                anchor='w'
            )
            label.grid(row=i+1, column=0, padx=10, pady=5, sticky='w')
            
            # Create value labels with placeholder text
            value_label = tk.Label(
                self.properties_frame,
                text="--",
                font=('Arial', 10),
                bg='white',
                anchor='w'
            )
            value_label.grid(row=i+1, column=1, padx=5, pady=5, sticky='w')
            
            # Store reference to value labels
            self.prop_labels[prop] = value_label

        # Create separator
        separator = tk.Frame(self.properties_frame, height=2, bg='gray')
        separator.grid(row=len(properties)+1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        #bind resizing event to update image size
        self.window.bind('<Configure>', self.on_resize)

        #bind clicking events
        self.main_frame.bind('<Button-1>', self.upload_image)
        self.image_label.bind('<Button-1>', self.upload_image)
        self.instruction.bind('<Button-1>', self.upload_image)

        #create tip frame in top right
        self.tip_frame = tk.Frame(
            self.window,
            bg='white',
            relief='solid',
            border=1,
            width=250,
            height=85
        )
        self.tip_frame.grid(row=0, column=1, padx=10, pady=0, sticky='ne')
        self.tip_frame.grid_propagate(False)

        #create tip label with initial text
        self.tip_label = tk.Label(
            self.tip_frame,
            text="Tip: Click anywhere in the image frame or use File → Upload to load an image",
            bg='white',
            justify='left',
            anchor='nw',
            wraplength=240
        )
        self.tip_label.grid(row=0, column=0, padx=5, pady=5, sticky='nw')

        #store our current image
        self.current_image = None
        
        # Store original image (before filters are applied)
        self.original_image = None
        
        # Track if filters have been applied
        self.filters_applied = False
        
        # Initialize image properties instance
        self.image_prop = ImageProperties()

        self.zmq_context = None
        self.zmq_socket = None

            # Add scaling menu after filter_menu is created
        self.scaling_menu = tk.Menu(
            self.menubar,
            tearoff=0,
            relief='solid',
            border=1,
            activeborderwidth=1
        )
        
        # Add scaling cascade menu
        self.menubar.add_cascade(
            label="Scaling",
            menu=self.scaling_menu,
            underline=-1
        )
        
        # Add scaling menu items
        self.scaling_menu.add_command(label="Resize Image", command=self.open_resize_dialog)
        self.scaling_menu.add_command(label="Crop Image", command=self.open_crop_dialog)
        self.scaling_menu.add_separator()
        self.scaling_menu.add_command(label="Revert to Original Size", command=self.revert_to_original)
        
        # Add ZMQ variables for scaling service
        self.scaling_zmq_context = None
        self.scaling_zmq_socket = None
        self.scaling_endpoint = "tcp://localhost:5556"
        
        # Add ZMQ configuration to your existing config
        try:
            self.zmq_port = self.image_prop.config.get('ZMQ_PORT', '5555')
            self.zmq_host = self.image_prop.config.get('ZMQ_HOST', 'localhost')
            self.zmq_endpoint = f"tcp://{self.zmq_host}:{self.zmq_port}"
        except:
            # Default values if config loading fails
            self.zmq_endpoint = "tcp://localhost:5555"

            # Add a new Adjustments menu
        self.adjustments_menu = tk.Menu(
            self.menubar,
            tearoff=0,
            relief='solid',
            border=1,
            activeborderwidth=1
        )
        
        # Add Adjustments cascade menu
        self.menubar.add_cascade(
            label="Adjustments",
            menu=self.adjustments_menu,
            underline=-1
        )
        

        self.adjustments_menu.add_command(label="Brightness", command=self.open_brightness_dialog)
        self.adjustments_menu.add_command(label="Contrast", command=self.open_contrast_dialog)
        
        # Add ZMQ variables for adjustments service
        self.adjustments_zmq_context = None
        self.adjustments_zmq_socket = None
        self.adjustments_endpoint = "tcp://localhost:5557"    

    def init_zmq(self):
        """Initialize ZMQ connection if not already done"""
        try:
            # Only initialize once
            if not hasattr(self, 'zmq_socket') or self.zmq_socket is None:
                print("Initializing ZMQ connection...")
                self.zmq_context = zmq.Context()
                self.zmq_socket = self.zmq_context.socket(zmq.REQ)
                self.zmq_socket.setsockopt(zmq.LINGER, 0)
                self.zmq_socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout
                self.zmq_socket.connect("tcp://localhost:5555")
            return True
        except Exception as e:
            print(f"ZMQ initialization error: {e}")
            return False
        
    def init_scaling_zmq(self):
        """Initialize ZMQ connection for scaling if not already done"""
        try:
            # Only initialize once
            if not hasattr(self, 'scaling_zmq_socket') or self.scaling_zmq_socket is None:
                print("Initializing Scaling ZMQ connection...")
                self.scaling_zmq_context = zmq.Context()
                self.scaling_zmq_socket = self.scaling_zmq_context.socket(zmq.REQ)
                self.scaling_zmq_socket.setsockopt(zmq.LINGER, 0)
                self.scaling_zmq_socket.setsockopt(zmq.RCVTIMEO, 3000)  # 3 second timeout
                self.scaling_zmq_socket.connect(self.scaling_endpoint)
            return True
        except Exception as e:
            print(f"Scaling ZMQ initialization error: {e}")
            return False
        
    def init_adjustments_zmq(self):
        """Initialize ZMQ connection for image adjustments if not already done"""
        try:
            # Only initialize once
            if not hasattr(self, 'adjustments_zmq_socket') or self.adjustments_zmq_socket is None:
                print("Initializing Adjustments ZMQ connection...")
                self.adjustments_zmq_context = zmq.Context()
                self.adjustments_zmq_socket = self.adjustments_zmq_context.socket(zmq.REQ)
                self.adjustments_zmq_socket.setsockopt(zmq.LINGER, 0)
                self.adjustments_zmq_socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout
                self.adjustments_zmq_socket.connect(self.adjustments_endpoint)
            return True
        except Exception as e:
            print(f"Adjustments ZMQ initialization error: {e}")
            return False

    def on_resize(self, event):
        #only resize if we have an image
        if hasattr(self, 'current_image') and self.current_image:
            #get the new dimensions
            frame_width = self.main_frame.winfo_width()
            frame_height = self.main_frame.winfo_height()
            
            #resize image to fit new dimensions
            self.resize_image(self.current_image, frame_width, frame_height)

    def resize_image(self, image, frame_width, frame_height):
        """Resize the image for display purposes"""
        # Calculate scaling factor
        img_width, img_height = image.size
        width_ratio = frame_width / img_width
        height_ratio = frame_height / img_height
        scale_factor = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Update PhotoImage
        photo = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

        

    def save_image(self):
        if hasattr(self, 'current_image') and self.current_image:
            if hasattr(self, 'current_file_path'):
                #save to the same file it was opened from
                self.current_image.save(self.current_file_path)
            else:
                #if no current file path, use save as
                self.save_image_as()
        else:
            tk.messagebox.showwarning("Warning", "No image to save!")

    def save_image_as(self):
        if hasattr(self, 'current_image') and self.current_image:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.current_image.save(file_path)
                self.current_file_path = file_path
        else:
            tk.messagebox.showwarning("Warning", "No image to save!")

    def update_properties(self, img_data):
        # Update properties display
        if img_data:
            self.prop_labels["Width:"].config(text=str(img_data['width']))
            self.prop_labels["Height:"].config(text=str(img_data['heigth']))  # Note: there's a typo in the original code
            self.prop_labels["Format:"].config(text=str(img_data['format']))
            self.prop_labels["Color Mode:"].config(text=str(img_data['color_mode']))
            
            # Format file size to be more readable
            size_kb = img_data['file_size'] / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.2f} MB"
            
            self.prop_labels["File Size:"].config(text=size_str)
            
            # Update tip with image dimensions
            self.update_tip(f"Current image: {img_data['width']}×{img_data['heigth']} pixels, {img_data['format']} format")

    def upload_image(self, event=None):
        #check if an image is already loaded and being displayed
        if hasattr(self, 'image_label') and self.current_image is not None:
            #show warning
            response = messagebox.askyesno(
                "Warning",
                "An image is already loaded. Do you want to replace it?\nAny unsaved changes will be lost.",
                icon='warning'
            )

            if not response:
                return

        #proceed with file selection
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        
        if file_path:
            #store the original image and file path
            self.current_image = Image.open(file_path)
            self.original_image = self.current_image.copy()  # Make a copy for restoration
            self.filters_applied = False
            self.current_file_path = file_path

            # Get image properties and update the properties panel
            img_data = self.image_prop.extract_data(file_path)
            if img_data:
                self.update_properties(img_data)
            
            #get current frame dimensions
            frame_width = self.main_frame.winfo_width()
            frame_height = self.main_frame.winfo_height()
            
            #resize image to fit frame
            self.resize_image(self.current_image, frame_width, frame_height)
            
            #hide instruction text
            self.instruction.grid_remove()

    def confirm_exit(self):
        #check if there's an image loaded and potentially unsaved changes
        if hasattr(self, 'current_image') and self.current_image is not None:
            response = messagebox.askyesno(
                "Exit",
                "Are you sure you want to exit?\nAny unsaved changes will be lost.",
                icon='warning'
            )
            if not response:
                return
        
        # Clean up ZMQ resources
        if hasattr(self, 'zmq_socket') and self.zmq_socket is not None:
            try:
                # Send quit message to server
                try:
                    self.zmq_socket.send_string("Q")
                    self.zmq_socket.recv(zmq.NOBLOCK)  # Don't block if server doesn't respond
                except:
                    pass
                self.zmq_socket.close()
            except:
                pass
        if hasattr(self, 'zmq_context') and self.zmq_context is not None:
            try:
                self.zmq_context.term()
            except:
                pass
        
                # Add cleanup for scaling ZMQ
        if hasattr(self, 'scaling_zmq_socket') and self.scaling_zmq_socket is not None:
            try:
                self.scaling_zmq_socket.close()
            except:
                pass
        
        if hasattr(self, 'scaling_zmq_context') and self.scaling_zmq_context is not None:
            try:
                self.scaling_zmq_context.term()
            except:
                pass

        # Add cleanup for adjustments ZMQ
        if hasattr(self, 'adjustments_zmq_socket') and self.adjustments_zmq_socket is not None:
            try:
                self.adjustments_zmq_socket.close()
            except:
                pass
        
        if hasattr(self, 'adjustments_zmq_context') and self.adjustments_zmq_context is not None:
            try:
                self.adjustments_zmq_context.term()
            except:
                pass    

        # Exit the application
        self.window.quit()       
        
    def update_tip(self, new_text):
        self.tip_label.config(text=new_text)
        
    def apply_grayscale(self):
        # Check if an image is loaded
        if not hasattr(self, 'current_image') or self.current_image is None:
            tk.messagebox.showwarning("Warning", "No image to apply filter to!")
            return
            
        # Show a processing message
        self.update_tip("Processing: Converting image to grayscale...")
        
        # Store the original image if no filters have been applied yet
        if not self.filters_applied and self.original_image is None:
            self.original_image = self.current_image.copy()
        
        try:
            # Try to use ZMQ for grayscale conversion
            if self.init_zmq():
                # Convert image to base64
                buffer = io.BytesIO()
                self.current_image.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Create request
                request = {
                    "command": "grayscale",
                    "image": img_base64
                }
                
                # Send request
                print("Sending grayscale request to ZMQ server...")
                self.zmq_socket.send_string(json.dumps(request))
                
                try:
                    # Receive response
                    response_json = self.zmq_socket.recv_string()
                    response = json.loads(response_json)
                    
                    if response.get("status") == "success":
                        # Process the successful response
                        img_data = base64.b64decode(response.get("image"))
                        grayscale_image = Image.open(io.BytesIO(img_data))
                        print("Successfully processed image via ZMQ")
                    else:
                        # Fall back to local processing
                        print(f"ZMQ server error: {response.get('error')}")
                        grayscale_image = self.current_image.convert('L').convert('RGB')
                except zmq.error.Again:
                    # Timeout - fall back to local processing
                    print("ZMQ timeout - using local processing")
                    grayscale_image = self.current_image.convert('L').convert('RGB')
            else:
                # ZMQ initialization failed - use local processing
                print("ZMQ unavailable - using local processing")
                grayscale_image = self.current_image.convert('L').convert('RGB')
        except Exception as e:
            # Any other error - use local processing
            print(f"Error in grayscale processing: {e}")
            grayscale_image = self.current_image.convert('L').convert('RGB')
        
        # Update the image
        self.current_image = grayscale_image
        self.filters_applied = True
        
        # Update the display
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        self.update_tip("Applied grayscale filter to image")
        
    def remove_filters(self):
        # Check if an image is loaded and filters have been applied
        if not hasattr(self, 'original_image') or self.original_image is None:
            tk.messagebox.showwarning("Warning", "No original image to restore!")
            return
        
        if not self.filters_applied:
            self.update_tip("No filters have been applied to remove")
            return
            
        # Restore the original image
        self.current_image = self.original_image.copy()
        self.filters_applied = False
        
        # Update the display
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        self.update_tip("All filters removed, original image restored")

    def open_resize_dialog(self):
        """Open a dialog to resize the image"""
        # Check if an image is loaded
        if not hasattr(self, 'current_image') or self.current_image is None:
            tk.messagebox.showwarning("Warning", "No image to resize!")
            return
        
        # Create a custom dialog
        resize_dialog = tk.Toplevel(self.window)
        resize_dialog.title("Resize Image")
        resize_dialog.geometry("400x350")  # Make it taller to ensure buttons are visible
        resize_dialog.resizable(False, False)
        resize_dialog.transient(self.window)
        resize_dialog.grab_set()
        
        # Get current image dimensions
        img_width, img_height = self.current_image.size
        
        # Create frame for dimension inputs
        dim_frame = tk.Frame(resize_dialog, padx=20, pady=20)
        dim_frame.pack(fill=tk.X)
        
        # Width label and entry
        tk.Label(dim_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, pady=5)
        width_var = tk.StringVar(value=str(img_width))
        width_entry = tk.Entry(dim_frame, textvariable=width_var, width=10)
        width_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        tk.Label(dim_frame, text="pixels").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        # Height label and entry
        tk.Label(dim_frame, text="Height:").grid(row=1, column=0, sticky=tk.W, pady=5)
        height_var = tk.StringVar(value=str(img_height))
        height_entry = tk.Entry(dim_frame, textvariable=height_var, width=10)
        height_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        tk.Label(dim_frame, text="pixels").grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        
        # Maintain aspect ratio checkbox
        maintain_aspect = tk.BooleanVar(value=True)
        aspect_check = tk.Checkbutton(dim_frame, text="Maintain aspect ratio", variable=maintain_aspect)
        aspect_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # Function to update the other dimension when one is changed (if maintain aspect ratio is checked)
        def update_dimensions(event, changed_dim):
            if maintain_aspect.get():
                aspect_ratio = img_width / img_height
                try:
                    if changed_dim == "width":
                        new_width = int(width_var.get())
                        height_var.set(str(int(new_width / aspect_ratio)))
                    else:
                        new_height = int(height_var.get())
                        width_var.set(str(int(new_height * aspect_ratio)))
                except ValueError:
                    pass  # Ignore conversion errors during typing
        
        width_entry.bind("<KeyRelease>", lambda e: update_dimensions(e, "width"))
        height_entry.bind("<KeyRelease>", lambda e: update_dimensions(e, "height"))
        
        # Add info text
        info_text = tk.Text(resize_dialog, height=6, width=40, wrap=tk.WORD, bg=self.window.cget('background'))
        info_text.pack(fill=tk.X, padx=20, pady=(0, 10))
        info_text.insert(tk.END, "Image Resizing Info:\n\n")
        info_text.insert(tk.END, "• Increasing size may reduce image quality.\n")
        info_text.insert(tk.END, "• Decreasing size will reduce file size.\n")
        info_text.insert(tk.END, "• Maintaining aspect ratio prevents distortion.\n")
        info_text.configure(state='disabled')
        
        # Create button frame with fixed height to ensure visibility
        button_frame = tk.Frame(resize_dialog, pady=10, height=50)
        button_frame.pack(fill=tk.X)
        button_frame.pack_propagate(False)  # Prevent shrinking
        
        # Cancel and resize buttons with explicit sizing
        cancel_button = tk.Button(button_frame, text="Cancel", command=resize_dialog.destroy, 
                                width=10, height=1)
        cancel_button.pack(side=tk.RIGHT, padx=20)
        
        def do_resize():
            try:
                new_width = int(width_var.get())
                new_height = int(height_var.get())
                
                if new_width <= 0 or new_height <= 0:
                    tk.messagebox.showerror("Error", "Width and height must be positive numbers")
                    return
                
                print(f"Resizing image to {new_width}x{new_height}...")
                self.resize_image_with_service(new_width, new_height, maintain_aspect.get())
                resize_dialog.destroy()
            except ValueError:
                tk.messagebox.showerror("Error", "Please enter valid dimensions")
        
        # Create the resize button with explicit sizing
        resize_button = tk.Button(button_frame, text="Resize", command=do_resize, 
                                width=10, height=1)
        resize_button.pack(side=tk.RIGHT, padx=5)
        
        # Add a debug label to ensure we can see what's happening
        debug_label = tk.Label(resize_dialog, text="Click Resize to apply changes", fg="blue")
        debug_label.pack(pady=(0, 10))
        
        # Center the dialog on the main window
        resize_dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - resize_dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - resize_dialog.winfo_height()) // 2
        resize_dialog.geometry(f"+{x}+{y}")

    def resize_image_with_service(self, width, height, maintain_aspect=True):
        """Resize the image using the ZMQ service or fallback to local processing"""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
        
        # Store original image if not already saved
        if self.original_image is None:
            self.original_image = self.current_image.copy()
        
        self.update_tip("Processing: Resizing image...")
        
        try:
            # Try to use ZMQ for resizing
            if self.init_scaling_zmq():
                # Convert image to base64
                buffer = io.BytesIO()
                self.current_image.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Create request
                request = {
                    "command": "resize",
                    "image": img_base64,
                    "width": width,
                    "height": height,
                    "maintain_aspect": maintain_aspect
                }
                
                # Send request
                print("Sending resize request to ZMQ server...")
                self.scaling_zmq_socket.send_string(json.dumps(request))
                
                try:
                    # Receive response
                    response_json = self.scaling_zmq_socket.recv_string()
                    response = json.loads(response_json)
                    
                    if response.get("status") == "success":
                        # Process the successful response
                        img_data = base64.b64decode(response.get("image"))
                        resized_image = Image.open(io.BytesIO(img_data))
                        print(f"Successfully resized image via ZMQ to {response.get('width')}x{response.get('height')}")
                    else:
                        # Fall back to local processing
                        print(f"ZMQ server error: {response.get('error')}")
                        resized_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
                except zmq.error.Again:
                    # Timeout - fall back to local processing
                    print("ZMQ timeout - using local processing")
                    resized_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
            else:
                # ZMQ initialization failed - use local processing
                print("ZMQ unavailable - using local processing")
                resized_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            # Any other error - use local processing
            print(f"Error in resize processing: {e}")
            resized_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Update the image
        self.current_image = resized_image
        self.filters_applied = True

        # Update the display
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        self.update_tip(f"Resized image to {width}x{height} pixels")
        
        # Update image properties
        self.update_image_properties()

    def open_crop_dialog(self):
        """Open a dialog to crop the image"""
        # Check if an image is loaded
        if not hasattr(self, 'current_image') or self.current_image is None:
            tk.messagebox.showwarning("Warning", "No image to crop!")
            return
        
        # Create a custom dialog
        crop_dialog = tk.Toplevel(self.window)
        crop_dialog.title("Crop Image")
        crop_dialog.transient(self.window)
        crop_dialog.grab_set()
        
        # Get current image dimensions
        img_width, img_height = self.current_image.size
        
        # Create a frame to hold everything
        main_frame = tk.Frame(crop_dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Calculate display size (scaled down if necessary)
        max_display_width = min(img_width, 800)
        max_display_height = min(img_height, 600)
        
        # Calculate scaling factor
        scale_factor = min(max_display_width / img_width, max_display_height / img_height)
        display_width = int(img_width * scale_factor)
        display_height = int(img_height * scale_factor)
        
        # Create a canvas to display the image and handle cropping
        canvas = tk.Canvas(main_frame, width=display_width, height=display_height, bg='white', relief='solid', bd=1)
        canvas.pack(pady=10)
        
        # Scale the image for display
        display_image = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        tk_image = ImageTk.PhotoImage(display_image)
        
        # Store the image to prevent garbage collection
        canvas.image = tk_image
        
        # Display the image
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        
        # Crop selection variables
        start_x, start_y = 0, 0
        end_x, end_y = 0, 0
        crop_rect = None
        dragging = False
        
        # Information label
        info_label = tk.Label(main_frame, text="Click and drag to select crop area")
        info_label.pack(pady=5)
        
        # Coordinates label
        coords_label = tk.Label(main_frame, text="Selected region: None")
        coords_label.pack(pady=5)
        
        # Function to update coordinates display
        def update_coords():
            # Convert canvas coordinates to actual image coordinates
            actual_start_x = int(start_x / scale_factor)
            actual_start_y = int(start_y / scale_factor)
            actual_end_x = int(end_x / scale_factor)
            actual_end_y = int(end_y / scale_factor)
            
            # Calculate selection dimensions
            width = abs(actual_end_x - actual_start_x)
            height = abs(actual_end_y - actual_start_y)
            
            coords_label.config(text=f"Selected region: {width}x{height} pixels")
        
        # Event handlers for crop selection
        def start_crop(event):
            nonlocal start_x, start_y, end_x, end_y, crop_rect, dragging
            start_x = canvas.canvasx(event.x)
            start_y = canvas.canvasy(event.y)
            end_x = start_x
            end_y = start_y
            
            # Create initial rectangle
            if crop_rect:
                canvas.delete(crop_rect)
            crop_rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)
            dragging = True
        
        def drag_crop(event):
            nonlocal end_x, end_y, crop_rect, dragging
            if dragging:
                end_x = canvas.canvasx(event.x)
                end_y = canvas.canvasy(event.y)
                
                # Ensure coordinates stay within image bounds
                end_x = max(0, min(end_x, display_width))
                end_y = max(0, min(end_y, display_height))
                
                # Update rectangle
                canvas.coords(crop_rect, start_x, start_y, end_x, end_y)
                update_coords()
        
        def end_crop(event):
            nonlocal dragging
            dragging = False
            update_coords()
        
        # Bind mouse events
        canvas.bind("<ButtonPress-1>", start_crop)
        canvas.bind("<B1-Motion>", drag_crop)
        canvas.bind("<ButtonRelease-1>", end_crop)
        
        # Create button frame with fixed height to ensure visibility
        button_frame = tk.Frame(main_frame, height=50)
        button_frame.pack(pady=10, fill=tk.X)
        button_frame.pack_propagate(False)  # Prevent shrinking
        
        # Add a clearly visible action message
        action_label = tk.Label(main_frame, text="Click 'Crop' button to apply changes", fg="blue", font=('Arial', 11, 'bold'))
        action_label.pack(pady=5)
        
        # Function to perform the crop
        def do_crop():
            print("do_crop function called")
            
            if not crop_rect:
                tk.messagebox.showwarning("Warning", "Please select an area to crop")
                return
            
            # Get the actual image coordinates (scale from display to actual image)
            x1 = int(min(start_x, end_x) / scale_factor)
            y1 = int(min(start_y, end_y) / scale_factor)
            x2 = int(max(start_x, end_x) / scale_factor)
            y2 = int(max(start_y, end_y) / scale_factor)
            
            # Ensure we have a valid crop region
            if x2 <= x1 or y2 <= y1:
                tk.messagebox.showwarning("Warning", "Please select a valid crop area")
                return
            
            print(f"Cropping image: {x1},{y1} to {x2},{y2}")
            # Perform the crop
            self.crop_image_with_service(x1, y1, x2, y2)
            crop_dialog.destroy()
        
        # Cancel and crop buttons with explicit sizing
        cancel_button = tk.Button(button_frame, text="Cancel", command=crop_dialog.destroy, 
                                width=10, height=1)
        cancel_button.pack(side=tk.RIGHT, padx=20)
        
        crop_button = tk.Button(button_frame, text="Crop", command=do_crop, 
                            width=10, height=1, bg="#e0e0ff")  # Light blue background
        crop_button.pack(side=tk.RIGHT, padx=5)
        
        # Size the dialog based on the canvas size with extra room for buttons
        crop_dialog.update_idletasks()
        dialog_width = display_width + 60
        dialog_height = display_height + 200  # Extra space for buttons
        crop_dialog.geometry(f"{dialog_width}x{dialog_height}")
        
        # Center the dialog
        x = self.window.winfo_x() + (self.window.winfo_width() - dialog_width) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - dialog_height) // 2
        crop_dialog.geometry(f"+{x}+{y}")

    def crop_image_with_service(self, left, top, right, bottom):
        """Crop the image using the ZMQ service or fallback to local processing"""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
        
        # Store original image if not already saved
        if self.original_image is None:
            self.original_image = self.current_image.copy()
        
        self.update_tip("Processing: Cropping image...")
        
        try:
            # Try to use ZMQ for cropping
            if self.init_scaling_zmq():
                # Convert image to base64
                buffer = io.BytesIO()
                self.current_image.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Create request
                request = {
                    "command": "crop",
                    "image": img_base64,
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom
                }
                
                # Send request
                print("Sending crop request to ZMQ server...")
                self.scaling_zmq_socket.send_string(json.dumps(request))
                
                try:
                    # Receive response
                    response_json = self.scaling_zmq_socket.recv_string()
                    response = json.loads(response_json)
                    
                    if response.get("status") == "success":
                        # Process the successful response
                        img_data = base64.b64decode(response.get("image"))
                        cropped_image = Image.open(io.BytesIO(img_data))
                        print(f"Successfully cropped image via ZMQ to {response.get('width')}x{response.get('height')}")
                    else:
                        # Fall back to local processing
                        print(f"ZMQ server error: {response.get('error')}")
                        cropped_image = self.current_image.crop((left, top, right, bottom))
                except zmq.error.Again:
                    # Timeout - fall back to local processing
                    print("ZMQ timeout - using local processing")
                    cropped_image = self.current_image.crop((left, top, right, bottom))
            else:
                # ZMQ initialization failed - use local processing
                print("ZMQ unavailable - using local processing")
                cropped_image = self.current_image.crop((left, top, right, bottom))
        except Exception as e:
            # Any other error - use local processing
            print(f"Error in crop processing: {e}")
            cropped_image = self.current_image.crop((left, top, right, bottom))
        
        # Update the image
        self.current_image = cropped_image
        self.filters_applied = True
        
        # Update the display (changed from resize_display_image to resize_image)
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        crop_width = right - left
        crop_height = bottom - top
        self.update_tip(f"Cropped image to {crop_width}x{crop_height} pixels")
        
        # Update image properties
        self.update_image_properties()

    def revert_to_original(self):
        """Revert the image to its original size"""
        if not hasattr(self, 'original_image') or self.original_image is None:
            tk.messagebox.showwarning("Warning", "No original image to revert to!")
            return
        
        # Restore the original image
        self.current_image = self.original_image.copy()
        
        # Update the display (changed from resize_display_image to resize_image)
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        img_width, img_height = self.current_image.size
        self.update_tip(f"Reverted to original size: {img_width}x{img_height} pixels")

        self.update_image_properties()

    def open_brightness_dialog(self):
        """Open dialog to adjust image brightness"""
        # Check if an image is loaded
        if not hasattr(self, 'current_image') or self.current_image is None:
            tk.messagebox.showwarning("Warning", "No image to adjust!")
            return
        
        # Create dialog window with fixed size
        brightness_dialog = tk.Toplevel(self.window)
        brightness_dialog.title("Adjust Brightness")
        brightness_dialog.geometry("400x550")
        brightness_dialog.minsize(400, 550)
        brightness_dialog.resizable(False, False)
        brightness_dialog.transient(self.window)
        brightness_dialog.grab_set()
        
        # Store original image for preview
        if not hasattr(self, 'original_for_preview') or self.original_for_preview is None:
            self.original_for_preview = self.current_image.copy()
        else:
            self.original_for_preview = self.current_image.copy()
        
        # Using a simpler pack layout
        main_frame = tk.Frame(brightness_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Preview section
        preview_label = tk.Label(main_frame, text="Preview:")
        preview_label.pack(anchor="w", pady=(0, 5))
        
        preview_size = (300, 200)
        preview_img = self.original_for_preview.resize(preview_size, Image.Resampling.LANCZOS)
        preview_photo = ImageTk.PhotoImage(preview_img)
        
        preview_canvas = tk.Canvas(main_frame, width=preview_size[0], height=preview_size[1], bg='white')
        preview_canvas.pack(pady=(0, 20))
        preview_canvas.create_image(preview_size[0]//2, preview_size[1]//2, image=preview_photo, anchor=tk.CENTER)
        preview_canvas.image = preview_photo
        
        # Slider section
        slider_label = tk.Label(main_frame, text="Brightness: 1.00x")
        slider_label.pack(anchor="w", pady=(10, 5))
        
        def on_slider_change(val):
            factor = float(val) / 50.0
            slider_label.config(text=f"Brightness: {factor:.2f}x")
            
            # Update preview
            try:
                enhancer = ImageEnhance.Brightness(self.original_for_preview)
                adjusted = enhancer.enhance(factor)
                adjusted_small = adjusted.resize(preview_size, Image.Resampling.LANCZOS)
                
                new_photo = ImageTk.PhotoImage(adjusted_small)
                preview_canvas.delete("all")
                preview_canvas.create_image(preview_size[0]//2, preview_size[1]//2, image=new_photo, anchor=tk.CENTER)
                preview_canvas.image = new_photo
            except Exception as e:
                pass  # Silently handle errors
        
        slider = tk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=on_slider_change)
        slider.set(50)  # Default middle value
        slider.pack(fill="x", pady=(0, 20))
        
        # Create a separator for visual distinction
        separator = tk.Frame(main_frame, height=2, bg="gray")
        separator.pack(fill="x", pady=10)
        
        # Apply button in its own frame to ensure visibility
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        def apply_brightness():
            factor = float(slider.get()) / 50.0
            self.adjust_brightness_with_service(factor)
            brightness_dialog.destroy()
        
        apply_btn = tk.Button(button_frame, text="APPLY CHANGES", command=apply_brightness,
                            width=20, height=2, bg="#aaddff", font=('Arial', 10, 'bold'))
        apply_btn.pack()
        
        # Center dialog
        brightness_dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - brightness_dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - brightness_dialog.winfo_height()) // 2
        brightness_dialog.geometry(f"+{x}+{y}")

    def open_contrast_dialog(self):
        """Open dialog to adjust image contrast"""
        # Check if an image is loaded
        if not hasattr(self, 'current_image') or self.current_image is None:
            tk.messagebox.showwarning("Warning", "No image to adjust!")
            return
        
        # Create dialog window with fixed size - ensure it's tall enough
        contrast_dialog = tk.Toplevel(self.window)
        contrast_dialog.title("Adjust Contrast")
        contrast_dialog.geometry("400x550")  # Same size as brightness dialog
        contrast_dialog.minsize(400, 550)    # Enforce minimum size
        contrast_dialog.resizable(False, False)
        contrast_dialog.transient(self.window)
        contrast_dialog.grab_set()
        
        # Store original image for preview
        if not hasattr(self, 'original_for_preview') or self.original_for_preview is None:
            self.original_for_preview = self.current_image.copy()
        else:
            self.original_for_preview = self.current_image.copy()
        
        # Use a ScrolledFrame if the image is very tall
        main_frame = tk.Frame(contrast_dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Preview section
        preview_label = tk.Label(main_frame, text="Preview:")
        preview_label.pack(anchor="w", pady=(0, 5))
        
        # Limit preview size
        preview_size = (300, 200)  # Fixed preview size regardless of image dimensions
        preview_img = self.original_for_preview.resize(preview_size, Image.Resampling.LANCZOS)
        preview_photo = ImageTk.PhotoImage(preview_img)
        
        preview_canvas = tk.Canvas(main_frame, width=preview_size[0], height=preview_size[1], bg='white')
        preview_canvas.pack(pady=(0, 20))
        preview_canvas.create_image(preview_size[0]//2, preview_size[1]//2, image=preview_photo, anchor=tk.CENTER)
        preview_canvas.image = preview_photo
        
        # Slider section
        slider_label = tk.Label(main_frame, text="Contrast: 1.00x")
        slider_label.pack(anchor="w", pady=(10, 5))
        
        def on_slider_change(val):
            factor = float(val) / 50.0
            slider_label.config(text=f"Contrast: {factor:.2f}x")
            
            # Update preview
            try:
                enhancer = ImageEnhance.Contrast(self.original_for_preview)
                adjusted = enhancer.enhance(factor)
                adjusted_small = adjusted.resize(preview_size, Image.Resampling.LANCZOS)
                
                new_photo = ImageTk.PhotoImage(adjusted_small)
                preview_canvas.delete("all")
                preview_canvas.create_image(preview_size[0]//2, preview_size[1]//2, image=new_photo, anchor=tk.CENTER)
                preview_canvas.image = new_photo
            except Exception as e:
                pass  # Silently handle errors
        
        slider = tk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=on_slider_change)
        slider.set(50)  # Default middle value
        slider.pack(fill="x", pady=(0, 20))
        
        # Create a separator for visual distinction
        separator = tk.Frame(main_frame, height=2, bg="gray")
        separator.pack(fill="x", pady=10)
        
        # Apply button in its own frame to ensure visibility
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        def apply_contrast():
            factor = float(slider.get()) / 50.0
            self.adjust_contrast_with_service(factor)
            contrast_dialog.destroy()
        
        apply_btn = tk.Button(button_frame, text="APPLY CHANGES", command=apply_contrast,
                        width=20, height=2, bg="#aaddff", font=('Arial', 10, 'bold'))
        apply_btn.pack()
        
        # Center dialog
        contrast_dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - contrast_dialog.winfo_width()) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - contrast_dialog.winfo_height()) // 2
        contrast_dialog.geometry(f"+{x}+{y}")

    def adjust_brightness_with_service(self, factor):
        """Adjust image brightness using ZMQ service or local processing"""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
        
        # Store original image if not already saved
        if self.original_image is None:
            self.original_image = self.current_image.copy()
        
        self.update_tip("Processing: Adjusting brightness...")
        
        try:
            # Try to use ZMQ for brightness adjustment
            if self.init_adjustments_zmq():
                # Convert image to base64
                buffer = io.BytesIO()
                self.current_image.save(buffer, format=getattr(self.current_image, 'format', 'PNG') or 'PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Create request
                request = {
                    "command": "brightness",
                    "image": img_base64,
                    "factor": factor
                }
                
                # Send request
                print("Sending brightness request to ZMQ server...")
                self.adjustments_zmq_socket.send_string(json.dumps(request))
                
                try:
                    # Receive response
                    response_json = self.adjustments_zmq_socket.recv_string()
                    response = json.loads(response_json)
                    
                    if response.get("status") == "success":
                        # Process the successful response
                        img_data = base64.b64decode(response.get("image"))
                        adjusted_image = Image.open(io.BytesIO(img_data))
                        print(f"Successfully adjusted brightness via ZMQ")
                    else:
                        # Fall back to local processing
                        print(f"ZMQ server error: {response.get('error')}")
                        enhancer = ImageEnhance.Brightness(self.current_image)
                        adjusted_image = enhancer.enhance(factor)
                except zmq.error.Again:
                    # Timeout - fall back to local processing
                    print("ZMQ timeout - using local processing")
                    enhancer = ImageEnhance.Brightness(self.current_image)
                    adjusted_image = enhancer.enhance(factor)
            else:
                # ZMQ initialization failed - use local processing
                print("ZMQ unavailable - using local processing")
                enhancer = ImageEnhance.Brightness(self.current_image)
                adjusted_image = enhancer.enhance(factor)
        except Exception as e:
            # Any other error - use local processing
            print(f"Error in brightness processing: {e}")
            enhancer = ImageEnhance.Brightness(self.current_image)
            adjusted_image = enhancer.enhance(factor)
        
        # Update the image
        self.current_image = adjusted_image
        self.filters_applied = True
        
        # Update the display
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        self.update_tip(f"Adjusted brightness to {factor:.2f}")
        
        # Update image properties
        self.update_image_properties()

    def adjust_contrast_with_service(self, factor):
        """Adjust image contrast using ZMQ service or local processing"""
        if not hasattr(self, 'current_image') or self.current_image is None:
            return
        
        # Store original image if not already saved
        if self.original_image is None:
            self.original_image = self.current_image.copy()
        
        self.update_tip("Processing: Adjusting contrast...")
        
        try:
            # Try to use ZMQ for contrast adjustment
            if self.init_adjustments_zmq():
                # Convert image to base64
                buffer = io.BytesIO()
                self.current_image.save(buffer, format=getattr(self.current_image, 'format', 'PNG') or 'PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Create request
                request = {
                    "command": "contrast",
                    "image": img_base64,
                    "factor": factor
                }
                
                # Send request
                print("Sending contrast request to ZMQ server...")
                self.adjustments_zmq_socket.send_string(json.dumps(request))
                
                try:
                    # Receive response
                    response_json = self.adjustments_zmq_socket.recv_string()
                    response = json.loads(response_json)
                    
                    if response.get("status") == "success":
                        # Process the successful response
                        img_data = base64.b64decode(response.get("image"))
                        adjusted_image = Image.open(io.BytesIO(img_data))
                        print(f"Successfully adjusted contrast via ZMQ")
                    else:
                        # Fall back to local processing
                        print(f"ZMQ server error: {response.get('error')}")
                        enhancer = ImageEnhance.Contrast(self.current_image)
                        adjusted_image = enhancer.enhance(factor)
                except zmq.error.Again:
                    # Timeout - fall back to local processing
                    print("ZMQ timeout - using local processing")
                    enhancer = ImageEnhance.Contrast(self.current_image)
                    adjusted_image = enhancer.enhance(factor)
            else:
                # ZMQ initialization failed - use local processing
                print("ZMQ unavailable - using local processing")
                enhancer = ImageEnhance.Contrast(self.current_image)
                adjusted_image = enhancer.enhance(factor)
        except Exception as e:
            # Any other error - use local processing
            print(f"Error in contrast processing: {e}")
            enhancer = ImageEnhance.Contrast(self.current_image)
            adjusted_image = enhancer.enhance(factor)
        
        # Update the image
        self.current_image = adjusted_image
        self.filters_applied = True
        
        # Update the display
        frame_width = self.main_frame.winfo_width()
        frame_height = self.main_frame.winfo_height()
        self.resize_image(self.current_image, frame_width, frame_height)
        
        # Update the tip
        self.update_tip(f"Adjusted contrast to {factor:.2f}")
        
        # Update image properties
        self.update_image_properties()    

    def update_image_properties(self):
        """Update the image properties panel after image modifications"""
        if hasattr(self, 'current_image') and self.current_image:
            try:
                # Save the current image to a temporary file
                temp_path = "temp_image.png"
                self.current_image.save(temp_path)
                
                # Get properties using the microservice
                img_data = self.image_prop.extract_data(temp_path)
                
                # Update properties panel
                if img_data:
                    self.update_properties(img_data)
                    
                # Remove the temporary file
                import os
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"Error updating image properties: {e}")    

    def open_simple_brightness_dialog(self):
        """Simplified test dialog"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Simple Brightness Test")
        dialog.geometry("300x150")
        
        def on_slider_change(val):
            print(f"Slider value changed to: {val}")
        
        label = tk.Label(dialog, text="Brightness:")
        label.pack(pady=10)
        
        # Very basic slider
        slider = tk.Scale(dialog, from_=0, to=100, orient=tk.HORIZONTAL, 
                        command=on_slider_change)
        slider.pack(fill=tk.X, padx=20)
        
        # Test button
        button = tk.Button(dialog, text="Test", 
                        command=lambda: print("Button clicked"))
        button.pack(pady=10)

    # Also add this test function
    def test_pil_enhance(self):
        if not hasattr(self, 'current_image') or self.current_image is None:
            print("No image loaded")
            return
            
        try:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Brightness(self.current_image)
            enhanced = enhancer.enhance(1.5)  # 50% brighter
            print("PIL enhancement successful")
            
            # Show the enhanced image temporarily
            self.current_image = enhanced
            frame_width = self.main_frame.winfo_width()
            frame_height = self.main_frame.winfo_height()
            self.resize_image(self.current_image, frame_width, frame_height)
        except Exception as e:
            print(f"PIL enhancement error: {e}")

    def run(self):
        self.window.mainloop()

    def test_slider_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Test Slider")
        dialog.geometry("300x150")
        
        print("Creating simple test dialog")
        
        # Create a label
        label = tk.Label(dialog, text="This is a test slider:")
        label.pack(pady=10)
        
        # Create a simple slider directly in the dialog
        print("Creating slider")
        slider = tk.Scale(dialog, from_=0, to=100, orient=tk.HORIZONTAL)
        print("Packing slider")
        slider.pack(padx=20, fill=tk.X)
        print("Slider packed")
        
        # Add a button
        button = tk.Button(dialog, text="Close", command=dialog.destroy)
        button.pack(pady=10)
        
        print("Dialog setup complete")



if __name__ == "__main__":
    image_viewer = ImageViewer()
    image_viewer.run()