#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk

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

        #create image frame with defined minimum size
        self.main_frame = tk.Frame(self.window, bg='white', width=1067, height=600)
        self.main_frame.grid(row=1, column=0, padx=20, pady=20, sticky='sw')
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

    def on_resize(self, event):
        #only resize if we have an image
        if hasattr(self, 'current_image') and self.current_image:
            #get the new dimensions
            frame_width = self.main_frame.winfo_width()
            frame_height = self.main_frame.winfo_height()
            
            #resize image to fit new dimensions
            self.resize_image(self.current_image, frame_width, frame_height)

    def resize_image(self, image, frame_width, frame_height):
        #calculate scaling factor
        img_width, img_height = image.size
        width_ratio = frame_width / img_width
        height_ratio = frame_height / img_height
        scale_factor = min(width_ratio, height_ratio)
        
        #calculate new dimensions
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        #update PhotoImage
        photo = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def upload_image(self, event=None):
        #check if image is already loaded
        if hasattr(self, 'current_image') and self.current_image:
            #show warning dialog
            response = messagebox.askyesno(
                "Warning",
                "An image is already loaded. Do you want to replace it?\nAny unsaved changes will be lost.",
                icon='warning'
            )
            #ff user clicks [No], return without doing anything
            if not response:
                return
        
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        
        if file_path:
            #store the original image
            self.current_image = Image.open(file_path)
            
            #get current frame dimensions
            frame_width = self.main_frame.winfo_width()
            frame_height = self.main_frame.winfo_height()
            
            #resize image to fit frame
            self.resize_image(self.current_image, frame_width, frame_height)
            
            #hide instruction text
            self.instruction.grid_remove()

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
            self.current_file_path = file_path
            
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
            if response:
                self.window.quit()
        else:
            #if no image is loaded, just exit
            self.window.quit()       
        
    def update_tip(self, new_text):
        self.tip_label.config(text=new_text)    

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    image_viewer = ImageViewer()
    image_viewer.run()