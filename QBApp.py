import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition

class QueryBuilder(BoxLayout):
	qb_button = ObjectProperty()
	screen_manager = ObjectProperty()
	toggleColumn = False
	def update_button(self, qb_button, main_layout):
		if not self.toggleColumn:
			self.toggleColumn = True
			column3 = BoxLayout(orientation='vertical', size_hint=(0.1, 1))
			for i in range(3):
				column3.add_widget(Label(text='column3item{}'.format(i)))
			main_layout.add_widget(column3)


	def change_screen(self, screen_name):
		self.screen_manager.current = screen_name
			
class QBApp(App):
	def build(self):
		return QueryBuilder()		

if __name__ == '__main__':
	QBApp().run()

