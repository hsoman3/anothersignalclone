import time
import sys
import socket  # Importing the socket module
import tkinter  # The python gui interface for Tk gui extension we 're using
import traceback
from tkinter import ttk  # Module providing access to the Tk themed widget set
import tkinter.messagebox
import tkinter.font
import tkinter.filedialog
from PIL import ImageTk, Image  # Importing the Python Imaging Library (Pillow)
import threading  # Module for high-level threading api in python
import base64  # Module for accessing base64 encoding features
from protocols.double_ratchet import KeyStore, Ratchet
import os
import pickle
import transport
import websockets.sync.client
import requests

# Every ttk object (representing a gui object..sort of) in the class has a style object associated with it for formatting, styling and beautification
# Entries are objects which appear like text boxes and we can take entries inside them,
# Labels are non modifiable objects that are just used to just mention or label other objects
# Buttons are objects that have a click functionaity which is on an event of a click can call some functions
# .grid functions are used to position the different objects that are created the before objects
RECV_BUFFER = 10000000
users = {}
messages = {}
global contacts


# Data recieved
class Application(tkinter.Tk):
    def load_user_keys(self, folder_path):

        # Iterate over each file in the folder
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".dat"):  # Check if the file is a .dat file
                file_path = os.path.join(folder_path, file_name)
                username = os.path.splitext(file_name)[0]  # Extract username from file name

                # Load ratchet key from the pickle file
                with open(file_path, 'rb') as file:
                    ratchet_key = pickle.load(file)

                # Store ratchet key in the dictionary with username as the key
                users[username] = ratchet_key

        # return user_keys

    def launch_app(self):
        # default function always run to generate the main
        # pickle_file_path = "./store/kb.pkl"  # Update this with your actual pickle file path
        dat_file_path = "./store/kb.dat"  # Update this with your actual .dat file path

        # Ensure directory exists for pickle file
        # pickle_dir = os.path.dirname(pickle_file_path)
        # os.makedirs(pickle_dir, exist_ok=True)

        # Ensure directory exists for .dat file
        dat_dir = os.path.dirname(dat_file_path)
        os.makedirs(dat_dir, exist_ok=True)

        if os.path.exists(dat_file_path):
            with open(dat_file_path, 'rb') as file:
                self.bob = pickle.load(file)
                # Add your code to process the unpickled data here
                print("Pickle file exists. Unpickled data:", self.bob)

        users_folder_path = "./store/users"  # Update this with the actual path to the users' folder

        # Load user keys from the folder
        self.load_user_keys(users_folder_path)
        print(users)

        self.title('Yet Another Signal Clone')  # Name of our Application

        self.frame = ttk.Frame(self)  # A default object frame of the Frame class of the ttk library

        self.frame.style = ttk.Style()

        # Initial frame contains two buttons: One for registration and one for Log In
        ttk.Style().configure("TButton", padding=6, relief="flat")
        self.reg_btn = ttk.Button(self.frame, text='New user?  Sign Up here!', command=self.reg_menu, takefocus=True)
        self.reg_btn.grid(row=2, column=2, padx=40, pady=30)
        self.client_button = ttk.Button(self.frame, text='Log In', command=self.client_menu, takefocus=True)
        self.client_button.grid(row=2, column=0, padx=40, pady=30)
        self.try_again_bool = False
        self.try_again_bool2 = False
        # Command that integrates different objects into a single parent object.
        self.frame.pack(fill=tkinter.BOTH, expand=True)

        self.theme_use = 'classic'

        self.frame.style.theme_use(self.theme_use)

        # mailoop command keeps on running this for some time continuously, else it disappears.
        self.mainloop()

    # The Registration Menu
    def reg_menu(self):
        # Previous menu's buttons destroyed
        if self.try_again_bool2:
            self.try_again2.destroy()
            self.un_error.destroy()
            self.try_again_bool2 = False
        self.client_button.destroy()
        self.reg_btn.destroy()

        # Entries of this frame are host, port name and password and corresponding labels and entries are created
        # self.host_entry_label = ttk.Label(self.frame, text = 'Server IP Address', justify = tkinter.RIGHT)
        # self.host_entry = ttk.Entry(self.frame)
        # self.port_entry_label = ttk.Label(self.frame, text = 'Port Number', justify = tkinter.RIGHT)
        # self.port_entry = ttk.Entry(self.frame)
        self.host = "127.0.0.1"  # Hardcoded IP address
        self.port = 9000
        self.reg_name_label = ttk.Label(self.frame, text='Username', justify=tkinter.RIGHT)
        self.reg_name_entry = ttk.Entry(self.frame)
        self.reg_pwd_label = ttk.Label(self.frame, text="Password", justify=tkinter.RIGHT)
        self.reg_pwd_entry = ttk.Entry(self.frame, show='*')

        # Register Button
        self.register_btn = ttk.Button(self.frame, text='Sign Up', command=self.reg_user, takefocus=True)

        # Forgetting the previous packed Buttons
        self.frame.pack_forget()

        self.title('Registration')

        # Positioning the labels and text boxes appropriately
        # self.host_entry_label.grid(row=0, column=0, pady=10,padx=5,sticky=tkinter.E)
        # self.host_entry.grid(row=0, column=1, pady=10,padx =5)
        # self.port_entry_label.grid(row=1,column=0,pady=10,padx=5,sticky=tkinter.E)
        # self.port_entry.grid(row=1,column=1,pady=10,padx=5)
        self.reg_name_label.grid(row=2, column=0, pady=10, padx=5, sticky=tkinter.E)
        self.reg_name_entry.grid(row=2, column=1, pady=10, padx=5)
        self.reg_pwd_label.grid(row=3, column=0, pady=10, padx=5, sticky=tkinter.E)
        self.reg_pwd_entry.grid(row=3, column=1, pady=10, padx=5)
        self.register_btn.grid(row=4, column=2, pady=10, padx=5)

        # self.host_entry.focus_set()                                                     # to decide where the cursor is set
        # self.register_btn.focus_set()

        self.frame.pack(fill=tkinter.BOTH, expand=True)

    # Registering a new user
    def reg_user(self):
        # self.host = self.host_entry.get()
        # self.port = self.port_entry.get()
        # self.port = int(self.port)
        self.username = self.reg_name_entry.get().rstrip()
        self.password = self.reg_pwd_entry.get().rstrip()

        # delete the objects created in the frame that it was called into
        # self.host_entry_label.destroy()
        # self.host_entry.destroy()
        # self.port_entry_label.destroy()
        # self.port_entry.destroy()
        self.reg_name_label.destroy()
        self.reg_name_entry.destroy()
        self.reg_pwd_label.destroy()
        self.reg_pwd_entry.destroy()
        self.register_btn.destroy()
        self.frame.pack_forget()

        try:
            var = requests.post('http://127.0.0.1:8000/registration',
                                data='username=' + self.username + '&password=' + self.password,
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
            var = var.status_code
            if var == 201:
                print("Success")
                self.bob = KeyStore()
                ltk_pk, spk_pk, otpks = self.bob.get_key_bundle()
                spk_sig = self.bob.sign_spk()
                msg = ltk_pk + spk_pk + spk_sig
                b = b''
                for byte in otpks:
                    b += byte
                msg += b
                var = requests.post('http://127.0.0.1:8000/keybundle/' + self.username,
                                    json={
                                        "key_bundle": base64.encodebytes(msg).decode()
                                    },
                                    headers={'Content-Type': 'application/json'})
                if var.status_code != 201:
                    self.reg_menu()
            else:
                print("Failure")
                self.reg_menu()

            # self.conn.send(str.encode(self.username + ' ' + self.password)) #Sending username and password for storing in the database
        except Exception as e:
            print(traceback.format_exc())
            self.reg_menu()  # Failing to send the username and password

        # conf = self.conn.recv()
        # if (conf == "500"):
        #
        #     self.un_error = ttk.Label(self.frame, text='Username already used', anchor=tkinter.CENTER,
        #                               justify=tkinter.CENTER)
        #     self.try_again2 = ttk.Button(self.frame, text='Try again', command=self.reg_menu)
        #     self.un_error.grid(row=0, column=1, pady=10, padx=5)
        #     self.try_again2.grid(row=1, column=1, pady=10, padx=5)
        #     self.try_again_bool2 = True
        #     self.frame.pack(fill=tkinter.BOTH, expand=True)
        #
        # else:
        #     self.client_menu()
        self.client_menu()

    # The Log in menu
    def client_menu(self):
        # Preious buttons destroyed
        self.client_button.destroy()
        self.reg_btn.destroy()
        if self.try_again_bool:
            self.try_again.destroy()
            self.wp_error.destroy()
            self.try_again_bool = False

        self.title('Log In')

        # Entries of this frame are host, port name and password and corresponding labels and entries are created
        # self.host_entry_label = ttk.Label(self.frame, text = 'Server IP Address', anchor = tkinter.W, justify = tkinter.LEFT)
        # self.host_entry = ttk.Entry(self.frame)
        # self.port_entry_label = ttk.Label(self.frame, text = 'Port Number', anchor = tkinter.W, justify = tkinter.LEFT)
        # self.port_entry = ttk.Entry(self.frame)
        self.name_entry_label = ttk.Label(self.frame, text='User name', anchor=tkinter.W, justify=tkinter.LEFT)
        self.name_entry = ttk.Entry(self.frame)
        self.pwd_entry_label = ttk.Label(self.frame, text='Password', anchor=tkinter.W, justify=tkinter.LEFT)
        self.pwd_entry = ttk.Entry(self.frame, show='*')

        # Attempt a Log in.
        self.launch_button = ttk.Button(self.frame, text='Log In', command=self.launch_client)

        # Positioning the labels and text boxes appropriately
        # self.host_entry_label.grid(row = 0, column = 0, pady = 10, padx = 5)
        # self.host_entry.grid(row = 0, column = 1, pady = 10, padx = 5)
        # self.port_entry_label.grid(row = 1, column = 0, pady = 10, padx = 5)
        # self.port_entry.grid(row = 1, column = 1, pady = 10, padx = 5)
        self.name_entry_label.grid(row=2, column=0, pady=10, padx=5)
        self.name_entry.grid(row=2, column=1, pady=10, padx=5)
        self.pwd_entry_label.grid(row=3, column=0, pady=10, padx=5)
        self.pwd_entry.grid(row=3, column=1, pady=10, padx=5)
        self.launch_button.grid(row=5, column=1, pady=10, padx=5)

        # self.host_entry.focus_set()

        self.frame.pack(fill=tkinter.BOTH, expand=True)

    # Main Chat window
    def launch_client(self):

        # #Obtaining the host address and port number
        # self.host = self.host_entry.get()
        # self.port = self.port_entry.get()
        # self.port = int(self.port)
        self.host = "127.0.0.1"  # Hardcoded IP address
        self.port = 9000
        self.name = self.name_entry.get()
        self.pwd = self.pwd_entry.get()

        # Destroying the previous labels and entries
        # self.host_entry_label.destroy()
        # self.host_entry.destroy()
        # self.port_entry_label.destroy()
        # self.port_entry.destroy()
        self.name_entry_label.destroy()
        self.name_entry.destroy()
        self.pwd_entry_label.destroy()
        self.pwd_entry.destroy()

        self.launch_button.destroy()
        self.frame.pack_forget()

        # creating socket for client
        # self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.conn.settimeout(2);
        f = 0
        var = requests.post('http://127.0.0.1:8000/authentication',
                            data='username=' + self.name + '&password=' + self.pwd,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if var.status_code == 200:
            print("Successful login")
        else:
            print("Failure to login")
            self.launch_client()
        # self.list_of_active_users = self.initial_setup() #Obtaining the list of active users on successful connection to the user
        # if self.list_of_active_users==-1:
        #     return 0
        self.flag = 0
        self.conn = websockets.sync.client.connect("ws://127.0.0.1:9000")
        self.conn.send(self.name)
        print('sent name to server')

        # MAIN WINDOW
        self.title('Yet Another Signal Clone')  # Window title
        self.should_quit = False
        self.protocol('WM_DELETE_WINDOW', self.client_quit)

        # FETCH ALL MESSAGES
        var = requests.get('http://127.0.0.1:8000/messages/' + self.name,
                           headers={'Content-Type': 'application/json'})
        print('################################', var.json()['messages'])

        for msg in var.json()['messages']:
            if msg['type'] == 'x3dh':
                sender = msg['by']
                content = base64.decodebytes(msg['content'].encode())
                (sk_bob, msg, ratchet_pub) = self.bob.x3dh_w_header(content[:128], content[128:])
                if msg == sender + ' is requesting permission to chat':
                    print("success")
                    users[sender] = Ratchet(sk_bob, dh_pub_key=ratchet_pub)
                    print('Ratchet created')
                    self.conn.send(sender)
                    self.conn.send('msg')
                    hdr, cph = users[sender].encrypt(self.name + ' has accepted your request to chat')
                    self.conn.send(hdr)
                    self.conn.send(cph)
            else:
                sender = msg['by']
                content = base64.decodebytes(msg['content'].encode())
                if sender not in messages.keys():
                    messages[sender] = []
                messages[sender].append(users[sender].decrypt(content[:128], content[128:]))

        # STYLISING
        s = ttk.Style()
        s.configure("TButton", background='burlywood3')
        s.configure('my.TFrame', background='old lace')
        s.configure('new.TFrame', background='navajo white')
        s.configure('new1.TFrame', background='ivory2')
        s.configure("TLabelframe", background='old lace', highlightbackground='old lace')

        # Frames Used in Chat Window
        self.chat_frame = ttk.Frame(self.frame, borderwidth=5, style='my.TFrame')  # for the actual display of chat
        self.clients_frame = ttk.Frame(self.frame, style='my.TFrame')  # for radio buttons
        self.entry_frame = ttk.Frame(self, style='my.TFrame')  # for input text
        self.button_frame = ttk.Frame(self.entry_frame, style='my.TFrame')

        # Fonts Used in Chat Window
        fonte = tkinter.font.Font(family='Arial', size=16, weight=tkinter.font.BOLD)
        s.configure('.', font=fonte)
        font1 = tkinter.font.Font(family="Comic Sans MS", size=16, weight=tkinter.font.BOLD)
        font2 = tkinter.font.Font(family="Arial", size=16, weight=tkinter.font.BOLD)
        self.font3 = tkinter.font.Font(family="Courier New", size=16, weight=tkinter.font.BOLD)
        self.chat_font = tkinter.font.Font(family="Helvetica", size=18, weight=tkinter.font.BOLD)

        # #MENU BAR
        # top=self.winfo_toplevel()
        # self.menubar = tkinter.Menu(top,font=tkinter.font.Font(size=11,weight=tkinter.font.BOLD))
        # top['menu']=self.menubar
        # self.filemenu=tkinter.Menu(self.menubar,tearoff=0)                            #FILE MENU
        # self.filemenu.add_command(label="Save Chat",command=self.save_history)
        # self.filemenu.add_separator()
        # self.filemenu.add_command(label="Exit",command=self.client_quit)
        # self.menubar.add_cascade(label="File",menu=self.filemenu)
        # self.contact= tkinter.Menu(self.menubar,tearoff=0)                            #CONTACT MENU
        # self.contact.add_command(label="Add Contact",command=self.add_contact)
        # self.contact.add_command(label="Delete Contact",command=self.del_contact)
        # self.menubar.add_cascade(label="Contact",menu=self.contact)
        # self.chat=tkinter.Menu(self.menubar,tearoff=0)                                #CHAT MENU
        # self.enable = dict();self.checks=[]
        # self.chat.add_command(label="Select Chatters",command=self.user_selection)
        # self.menubar.add_cascade(label="Chat",menu=self.chat)

        # TEXT CHAT WINDOW
        self.chat_text = tkinter.Text(self.chat_frame, state=tkinter.DISABLED)
        self.scroll = tkinter.Scrollbar(self.chat_frame)  # Adding Scroll Bar to chat window
        self.scroll.configure(command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=self.scroll.set)

        # TAKING THE IMAGES REQUIRED FOR CHAT ICONS
        self.img = ImageTk.PhotoImage(Image.open('Images/send2.png'))
        self.img1 = ImageTk.PhotoImage(Image.open('Images/file.png'))
        self.img2 = ImageTk.PhotoImage(Image.open('Images/user.png'))

        # MESSAGE ENTRY WINDOW
        self.chat_entry = ttk.Entry(self.entry_frame, font=font2)  # Text Entry Widget
        self.scroll1 = tkinter.Scrollbar(self.entry_frame, orient=tkinter.HORIZONTAL)  # Adding ScrollBar
        self.scroll1.configure(command=self.chat_entry.xview)
        self.chat_entry.configure(xscrollcommand=self.scroll1.set)
        self.send_button = ttk.Button(self.button_frame, image=self.img)  # Button for sending text message
        self.browsebutton = ttk.Button(self.button_frame, image=self.img1,
                                       command=self.browse)  # Button for browsing multimedia
        self.send_button.bind('<Button-1>', self.send)  # press button-1 to send messages
        self.chat_entry.bind('<Return>', self.send)  # Alternate to sending messages, hitting the return button

        # CLIENT FRAME
        self.user_icon = ttk.Label(self.clients_frame, image=self.img2, background='light blue', text=self.name,
                                   compound="top", font=self.font3, anchor=tkinter.E)  # Code for the Display Icon
        self.frame.pack(side=tkinter.TOP, fill=tkinter.BOTH,
                        expand=True)  # Packing the above created objects and giving them positions while packing
        self.user_icon.pack(side=tkinter.TOP)

        # SERVER INFO
        # self.server_l=ttk.Labelframe(self.clients_frame,text="Server Info",labelanchor=tkinter.NW,padding=20,borderwidth=2)
        # self.server_info1=ttk.Label(self.server_l,background='old lace',text="Server IP : "+self.host+'\n\n'+"Server Port: "+str(self.port),font=self.font3)
        # self.server_l.pack(side=tkinter.TOP,pady=40)
        # self.server_info1.pack()

        # TAB SECTION
        s.configure('TNotebook', background='old lace', borderwidth=1)
        self.tabs = ttk.Notebook(self.clients_frame, height=20, padding=10)
        self.tabs.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        # self.f1=ttk.Frame(self.clients_frame,style="new.TFrame")
        self.f2 = ttk.Frame(self.clients_frame, style="new1.TFrame")
        # self.tabs.add(self.f1,text="Online Users")
        self.tabs.add(self.f2, text="Contacts")
        # ONLINE USERS#
        # self.online=[];j=0
        # for i in self.list_of_active_users:
        #     # print(i)
        #     self.enable[i]=tkinter.IntVar()
        #     # self.enable[i].set(0)
        #     l=ttk.Label(self.f1,padding=10,text=i,justify=tkinter.LEFT,font=self.font3,foreground='forest green',background='navajo white')
        #     l.grid(row=j,column=0,sticky=tkinter.W)
        #     self.online.append(l)
        #     j=j+1

        # CONTACTS#

        self.contact_label = [];
        # with open('textfiles/contact.txt', 'rb') as file:
        #     contacts = (file.read()).decode()
        #     print('Contacts: ', contacts)
        # self.contacts = contacts.split(' ')
        self.selected_contact = tkinter.StringVar()

        # Create a Combobox to display the contacts
        self.contact_combobox = ttk.Combobox(self.f2, textvariable=self.selected_contact, font=self.font3,
                                             foreground='gray49', background='old lace')
        self.contact_combobox.grid(row=0, column=0, sticky=tkinter.W)
        # self.contact_combobox['values'] = self.contacts

        var = requests.get('http://127.0.0.1:8000/users',
                           headers={'Content-Type': 'application/json'})
        var = var.json()['users']
        self.contacts = []
        self.contacts_with_status = []
        for user in var:
            if self.name == user['user']:
                continue
            self.contacts.append(user['user'])
            if user['active']:
                self.contacts_with_status.append(user['user'] + ' *')
            else:
                self.contacts_with_status.append(user['user'])
        self.num_contacts = len(var) - 1

        self.contact_combobox['values'] = self.contacts_with_status
        # Bind a callback function to handle selection changes
        self.contact_combobox.bind("<<ComboboxSelected>>", self.handle_contact_selection)

        # PACKING ABOVE CREATED widgets                      #The order of packing of widgets may be arbitrary to ensure proper layout.
        self.clients_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.chat_frame.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True)
        self.send_button.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.browsebutton.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.button_frame.pack(side=tkinter.RIGHT)
        self.scroll1.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.chat_entry.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.entry_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.chat_text.pack(fill=tkinter.BOTH, expand=True)
        self.chat_entry.focus_set()

        self.clientchat_thread = threading.Thread(name='clientchat',
                                                  target=self.clientchat)  # for client we will intiate a thread to display chat
        self.clientchat_thread.start()
        # self.clientchat_thread.join()

    def handle_contact_selection(self, event):
        selected_contact = self.selected_contact.get()
        if '*' in selected_contact:
            selected_contact = selected_contact[:-2]

        if selected_contact not in users:
            var = requests.get('http://127.0.0.1:8000/keybundle/' + selected_contact,
                               headers={'Content-Type': 'application/x-www-form-urlencoded'})
            bundle = base64.decodebytes(var.json()['key_bundle'].encode())
            ltk = bundle[:32]
            spk = bundle[32:64]
            sig = bundle[64:128]
            arr = []

            _sum = 128
            while _sum + 32 >= len(bundle):
                arr.append(bundle[_sum:_sum + 32])
                _sum = _sum + 32

            arr = arr[0] if len(arr) else None
            (sk_alice, header, cipher, ratchet_pair) = self.bob.x3dh_w_key_bundle(
                self.name + ' is requesting permission to chat', (ltk, spk, sig, arr))
            users[selected_contact] = Ratchet(sk_alice, ratchet_pair)
            print('Ratchet generated')
            print(users.keys())

            self.conn.send(selected_contact)
            self.conn.send('x3dh')
            self.conn.send(header)
            self.conn.send(cipher)
            print('sending ratchet message')

            self.chat_text.config(state=tkinter.NORMAL)
            self.chat_text.insert(tkinter.END,
                                  'Waiting for ' + selected_contact + 'to accept request to chat...' + '\n',
                                  ('tag{0}'.format(2)))
            self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                                      font=self.chat_font)
            self.chat_text.config(state=tkinter.DISABLED)
            self.chat_text.see(tkinter.END)

        print(messages)
        if selected_contact in messages:
            for msg in messages[selected_contact]:
                self.chat_text.config(state=tkinter.NORMAL)
                self.chat_text.insert(tkinter.END, msg + '\n', ('tag{0}'.format(2)))
                self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                                          font=self.chat_font)
                self.chat_text.config(state=tkinter.DISABLED)
                self.chat_text.see(tkinter.END)

    # RECEIVER SELECTION WINDOW
    def user_selection(self):
        self.root = tkinter.Toplevel(self)
        self.root.title("User Selection")
        frame = tkinter.Frame(self.root)
        frame1 = tkinter.Frame(frame)
        label1 = tkinter.Label(frame1, text="Select the users you want to connect to:", compound=tkinter.LEFT,
                               font=('Helvetica', '20'), justify=tkinter.CENTER)
        label1.pack(side=tkinter.TOP, fill=tkinter.X)  # LABEL at the top
        frame1.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        frame2 = tkinter.Frame(self.root, borderwidth=10)
        i = 0
        for client in self.list_of_active_users:
            ch = tkinter.Checkbutton(frame2, text=client, variable=self.enable[client], borderwidth=0, pady=10,
                                     justify=tkinter.LEFT, font=('Courier New', 19), foreground='gray30')
            ch.grid(column=0, row=i, sticky=tkinter.W)
            i = i + 1
        frame3 = tkinter.Frame(frame2, borderwidth=10)
        b = tkinter.Button(frame3, text="Connect", justify=tkinter.CENTER, font=("Helvetica", '14'), padx=6, pady=6,
                           command=self.root.withdraw)
        b.pack()  # Button for connection and exiting this window
        frame3.grid(row=i, column=1, columnspan=2, sticky=tkinter.S)
        frame2.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=True)
        frame.pack(fill=tkinter.BOTH, expand=True)

    # CONTACT ADDITION WINDOW
    def add_contact(self):
        self.root = tkinter.Toplevel(self)
        self.root.title("Contact Addition")
        label1 = tkinter.Label(self.root, text="Enter the Contact Details:", font=('Helvetica', 20),
                               justify=tkinter.CENTER, pady=10)
        label1.grid(row=0, columnspan=2)
        label2 = tkinter.Label(self.root, text="Username", font=("Courier New", 14), justify=tkinter.RIGHT, pady=15)
        label2.grid(row=1, column=0)
        self.contact = tkinter.StringVar()
        self.contact.set("Type Username")
        entry1 = tkinter.Entry(self.root, textvariable=self.contact)
        entry1.grid(row=1, column=1)
        entry1.bind("<Return>", self.add)

    def add(self, event):
        if self.contact.get() in self.contacts:
            tkinter.messagebox.showwarning(title="Contact Exists", message="The Contact already exists")
            self.root.withdraw()
        with open("textfiles/contact.txt", "a") as file:
            file.write(" " + self.contact.get())
        l = ttk.Label(self.f2, padding=10, text=self.contact.get(), justify=tkinter.LEFT, font=self.font3,
                      foreground='gray49',
                      background='ivory2')  # l.grid(row=self.num_contacts,column=0,sticky=tkinter.W)
        l.grid(row=self.num_contacts, column=0, sticky=tkinter.W)
        self.contact_label.append(l)
        self.contacts.append(self.contact.get())
        self.num_contacts += 1
        self.root.withdraw()

    # CONTACT DELETION WINDOW
    def del_contact(self):
        self.root = tkinter.Toplevel(self)
        self.root.title("Contact Deletion")
        label1 = tkinter.Label(self.root, text="Enter the Contact to be removed:", font=('Helvetica', 20),
                               justify=tkinter.CENTER, pady=10)
        label1.grid(row=0, columnspan=2, column=0)
        label2 = tkinter.Label(self.root, text="Username", font=("Courier New", 14), justify=tkinter.LEFT, pady=15)
        label2.grid(row=1, column=0)
        self.remove1 = tkinter.StringVar()
        self.remove1.set("Type Username")
        entry1 = tkinter.Entry(self.root, textvariable=self.remove1)
        entry1.grid(row=1, column=1)
        entry1.bind("<Return>", self.remove)

    def remove(self, event):
        # print(self.contacts,self.remove1.get())
        try:
            self.contacts.remove(self.remove1.get())
        except:
            print(traceback.format_exc())
            tkinter.messagebox.showwarning(title="No Contact", message="No such contact exists")
            self.root.withdraw()
            return
        for i in self.contact_label:
            i.destroy()
        self.contact_label.clear()
        j = 0
        for i in self.contacts:
            l = ttk.Label(self.f2, padding=10, text=i, justify=tkinter.LEFT, font=self.font3, foreground='gray49',
                          background='ivory2')
            l.grid(row=j, column=0, sticky=tkinter.W)
            self.contact_label.append(l)
            j = j + 1
        self.num_contacts = j
        remove2 = ' '.join(self.contacts)
        # with open('textfiles/contact.txt', 'wb') as file:
        #     file.write(remove2.encode())
        self.root.withdraw()

    # Helper Function for sending messages
    def browse(self):
        self.mmfilename = tkinter.filedialog.askopenfilename()
        self.multimedia_send()

    def send(self, event):
        message = self.chat_entry.get()
        contact = self.selected_contact.get()
        if '*' in contact:
            contact = contact[:-2]
        header, cipher = users[contact].encrypt(message)

        print('Sending encrypted message')
        self.conn.send(contact)
        self.conn.send('msg')
        self.conn.send(header)
        self.conn.send(cipher)
        print('Sent encrypted message')
        # data = ""
        # for client in self.list_of_active_users:
        #     if self.enable[client].get() == 1:
        #         data = data + "@" + client + ' '
        # if data == "":
        #     tkinter.messagebox.showwarning(title="No Connection", message="Connect To Some User")
        #     return
        # data = data + ':'
        # data = data + message

        self.chat_entry.delete(0, tkinter.END)  # Emptying chat entry box
        #
        # self.conn.send(data.encode())  # Sending the encoded data to the server

        self.chat_text.config(state=tkinter.NORMAL)
        self.chat_text.insert(tkinter.END, self.name + ':' + message + '\n', ('tag{0}'.format(1)))
        self.chat_text.tag_config('tag{0}'.format(1), justify=tkinter.RIGHT, foreground='RoyalBlue3',
                                  font=self.chat_font)
        self.chat_text.config(
            state=tkinter.DISABLED)  # Again Disabling the edit functionality so that the user cannot edit it
        self.chat_text.see(tkinter.END)  # Enables the user to see the edited chat chat

    def multimedia_send(self):
        filename = self.mmfilename

        with open(filename, "rb") as file:
            encoded_string = (base64.b64encode(file.read())).decode()

        data = "^"
        for client in self.list_of_active_users:
            if self.enable[client].get() == 1:
                data = data + "@" + client + ' '

        data = data + ':'
        data = data + filename + ':'
        data_to_send = data + encoded_string

        # data_to_display = '^@'+dest+':'+ filename
        # data_to_send = data_to_display + ':' + encoded_string

        self.chat_entry.delete(0, tkinter.END)  # Emptying the chat entry box
        # self.conn.send(data_to_send.encode())

        self.chat_text.config(state=tkinter.NORMAL)
        self.chat_text.insert(tkinter.END, self.name + ':' + filename + '\n', ('tag{0}'.format(1)))
        self.chat_text.tag_config('tag{0}'.format(1), justify=tkinter.RIGHT, foreground='RoyalBlue3',
                                  font=self.chat_font)
        self.chat_text.config(
            state=tkinter.DISABLED)  # Again Disabling the edit functionality so that the user cannot edit it
        self.chat_text.see(tkinter.END)  # Enables the user to see the edited chat chat

    # Client Thread Target
    def clientchat(self):
        while not self.should_quit:  # If we are not in the 'quit' state then do :
            try:

                sender = self.conn.recv()
                type = self.conn.recv()
                print('################# sender type #######################', sender, type)

                if sender == 'server' and type == 'add':
                    new_contact = self.conn.recv()
                    if new_contact not in self.contacts:
                        self.contacts.append(new_contact)
                    if new_contact + ' *' not in self.contacts_with_status and new_contact in self.contacts_with_status:
                        self.contacts_with_status.remove(new_contact)
                        self.contacts_with_status.append(new_contact + ' *')
                    elif new_contact not in self.contacts_with_status:
                        self.contacts_with_status.append(new_contact + ' *')

                    self.contact_combobox['values'] = self.contacts_with_status

                elif sender == 'server' and type == 'remove':
                    new_contact = self.conn.recv()
                    self.contacts_with_status.remove(new_contact + ' *')
                    self.contacts_with_status.append(new_contact)
                    self.contact_combobox['values'] = self.contacts_with_status

                elif type == 'x3dh':
                    header = self.conn.recv()
                    cipher = self.conn.recv()
                    print('############# header cipher #################', header, cipher)
                    (sk_bob, msg, ratchet_pub) = self.bob.x3dh_w_header(header, cipher)
                    if msg == sender + ' is requesting permission to chat':
                        print("success")
                        users[sender] = Ratchet(sk_bob, dh_pub_key=ratchet_pub)
                        print('Ratchet created')

                        self.conn.send(sender)
                        self.conn.send('msg')
                        hdr, cph = users[sender].encrypt(sender + ' has accepted your request to chat')
                        self.conn.send(hdr)
                        self.conn.send(cph)
                        continue

                else:
                    header = self.conn.recv()
                    cipher = self.conn.recv()
                    print('cipher ', cipher)
                    print('header ', header)
                    msg = users[sender].decrypt(header, cipher)

                    contact = self.selected_contact.get()
                    if '*' in contact:
                        contact = contact[:-2]
                    print('decrypted message ', msg)
                    print('sender and contact', sender, contact)
                    print(sender == contact)

                    if sender == contact:
                        self.chat_text.config(state=tkinter.NORMAL)
                        self.chat_text.insert(tkinter.END, msg + '\n', ('tag{0}'.format(2)))
                        self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                                                  font=self.chat_font)
                        self.chat_text.config(state=tkinter.DISABLED)
                        self.chat_text.see(tkinter.END)
                    else:
                        if sender not in messages.keys():
                            messages[sender] = []
                        messages[sender].append(msg)

            except Exception as e:
                print(traceback.format_exc())
                continue

    # Helper function for quit option
    def client_quit(self):
        if tkinter.messagebox.askokcancel(title="Quit Window", message="Do you really want to quit?"):
            if self.bob:
                directory = './store'
                if not os.path.exists(directory):
                    os.makedirs(directory)

                # Specify the file path
                file_path = os.path.join(directory, 'kb.dat')

                # Serialize and save the key bundle
                with open(file_path, 'wb') as file:
                    pickle.dump(self.bob, file)

            if len(users.keys()) != 0:
                if not os.path.exists('./store/users'):
                    os.makedirs('./store/users')

                # Specify the file path
                for user in users.keys():
                    file_path = os.path.join('./store/users', user + '.dat')

                    # Serialize and save the key bundle
                    with open(file_path, 'wb') as file:
                        pickle.dump(users[user], file)
            self.should_quit = True
            self.conn.close()
            self.clientchat_thread.join()
            self.destroy()
        else:
            pass


# DRIVER
if __name__ == '__main__':
    app = Application()

    app.launch_app()  # Launching the app

