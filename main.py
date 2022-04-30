'''
Created on 6 avr. 2022

@author: YASSI
'''
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty, StringProperty, NumericProperty

from plyer import accelerometer
from plyer import sms
from plyer import gps
from kivy_garden.graph import Graph, MeshLinePlot
from kivy.clock import mainthread
from kivy.utils import platform

class PresplashWin(Screen):
    pass

class AccelerometerWin(Screen):
    
    graph_added = BooleanProperty(False)
    phone = StringProperty("")
    email = StringProperty("")
    gps_data = StringProperty("")
    x_crash_val = NumericProperty()
    y_crash_val = NumericProperty()
    z_crash_val = NumericProperty()
    
    def __init__(self, **kwargs): 
        super(Screen, self).__init__(**kwargs)
        self.sensorEnabled = False

    def do_toggle(self):
        screen = self.manager.get_screen("presplash")
        self.phone = screen.ids.phone.text    

        try:
            if not self.sensorEnabled:
                accelerometer.enable()
                Clock.schedule_interval(self.get_acceleration, 1 / 20)

                self.sensorEnabled = True
                self.ids.toggle_button.text = "Stop Accelerometer"
                #appData.start(1000, 0)
            else:
                accelerometer.disable()
                Clock.unschedule(self.get_acceleration)

                self.sensorEnabled = False
                self.ids.toggle_button.text = "Start Accelerometer"
                #appData.stop()
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            status = "Accelerometer is not implemented for your platform"
            self.ids.accel_status.text = status

            
    def show_graph(self):
        if (not self.graph_added):
            self.graph_added = True
            self.add_graph()
            Clock.schedule_interval(self.plot_acceleration, 1 / 50)
            self.ids.graph_button.text = "Hide Graph"
                        
        elif (self.ids.graph_plot.size_hint_y == .7):
            self.ids.graph_plot.size_hint_y = .00001
            Clock.unschedule(self.plot_acceleration)
            self.ids.graph_button.text = "Show Graph"
            self.ids.graph_plot.remove_widget(self.graph)
        
        else:
            self.ids.graph_plot.size_hint_y = .7
            Clock.schedule_interval(self.plot_acceleration, 1 / 50)
            self.ids.graph_button.text = "Hide Graph"
            self.add_graph()
        
    def add_graph(self):
        self.graph = Graph(xmin=0, xmax=100, 
                           ymin=-15, ymax=20,
                           y_grid_label=True, x_grid_label=True,
                           xlabel='', ylabel='')
        self.ids.graph_plot.add_widget(self.graph)
        self.ids.graph_plot.size_hint_y = .7
        
        self.plot = []
        self.plot.append(MeshLinePlot(color=[237/255, 248/255, 68/255, 1])) 
        self.plot.append(MeshLinePlot(color=[68/255, 248/255, 98/255, 1])) 
        self.plot.append(MeshLinePlot(color=[102/255, 204/255, 1, 1])) 
        
        self.reset_plots()

        for plot in self.plot:
            self.graph.add_plot(plot)

    def reset_plots(self):
        for plot in self.plot:
            plot.points = [(0,0)]

        self.counter = 1
            
    def get_acceleration(self, dt):
        val = accelerometer.acceleration[:3]
        
        if isinstance(App.get_running_app().root_window.children[0], Popup):
            sms.send(recipient=self.phone, message="Accident Alert !\n\n' Crash Detected '\n\nGPS Location :\n\n"+self.gps_data)
            
        if not val == (None, None, None):
            self.ids.x_label.text = "X axis : " + str(val[0])
            self.ids.y_label.text = "Y axis : " + str(val[1])
            self.ids.z_label.text = "Z axis : " + str(val[2])
            
            if (abs(val[0])>25 or abs(val[1])>25 or abs(val[2])>35):
                Clock.schedule_once(self.test_crash, 20)
                Clock.schedule_once(self.ensure_crash, 10)

    def test_crash(self, dt):
        val = accelerometer.acceleration[:3]
        self.x_crash_val = abs(val[0]) + 0.1
        self.y_crash_val = abs(val[1]) + 0.1
        self.z_crash_val = abs(val[2]) + 0.1
                    
    
    def ensure_crash(self, dt):
        val = accelerometer.acceleration[:3]
        x_val = self.x_crash_val - abs(val[0])
        y_val = self.y_crash_val - abs(val[1])
        z_val = self.z_crash_val - abs(val[2])
        
        if (x_val < 0.1 and y_val < 0.1 and z_val < 0.1):
            popup = PopupWin()
            popup.open()
    
    def plot_acceleration(self, dt):
        if (self.counter == 100):
            # We re-write our points list if number of values exceed 100.
            # ie. Move each timestamp to the left.
            for plot in self.plot:
                del(plot.points[0])
                plot.points[:] = [(i[0] - 1, i[1]) for i in plot.points[:]]
        
            self.counter = 99
        
        val = accelerometer.acceleration[:3]
        
        if(not val == (None, None, None)):
            self.plot[0].points.append((self.counter, val[0]))
            self.plot[1].points.append((self.counter, val[1]))
            self.plot[2].points.append((self.counter, val[2]))
        
        self.counter += 1

class PopupWin(Popup):
    pass

class Screen_Manager(ScreenManager):
    pass




class AccidentAlertApp(App):

    gps_location = StringProperty('Undefined')
    gps_status = StringProperty('Click Start to get GPS location updates')

    def request_android_permissions(self):
        """
        Since API 23, Android requires permission to be requested at runtime.
        This function requests permission and handles the response via a
        callback.
        The request will produce a popup if permissions have not already been
        been granted, otherwise it will do nothing.
        """
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            """
            Defines the callback to be fired when runtime permission
            has been granted or denied. This is not strictly required,
            but added for the sake of completeness.
            """
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([Permission.ACCESS_COARSE_LOCATION,
                             Permission.ACCESS_FINE_LOCATION, 
                             Permission.SEND_SMS], callback)
        # # To request permissions without a callback, do:
        # request_permissions([Permission.ACCESS_COARSE_LOCATION,
        #                      Permission.ACCESS_FINE_LOCATION])

    def build(self):
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'

        if platform == "android":
            print("gps.py: Android detected. Requesting permissions")
            self.request_android_permissions()

        return Builder.load_file("main.kv")

    def start(self, minTime, minDistance):
        gps.start(minTime, minDistance)

    def stop(self):
        gps.stop()

    @mainthread
    def on_location(self, **kwargs):
        self.gps_location = '\n'.join([
            ' {} = {}'.format(k, v) for k, v in kwargs.items()])

    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(1000, 0)
        pass

#appData = AccidentAlertApp()

if __name__ == '__main__':
    AccidentAlertApp().run()