import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition

class ResultScreen(BoxLayout):
	pass

class ScreenManagement(ScreenManager):
	pass

class QueryBuilderScreen(BoxLayout):
	qb_button = ObjectProperty()
	#screen_manager = ObjectProperty()
	toggleColumn = False
	def update_button(self, qb_button, main_layout):
		
		if not self.toggleColumn:
			self.toggleColumn = True
			column3 = BoxLayout(orientation='vertical', size_hint=(0.1, 1))
			for i in range(3):
				column3.add_widget(Label(text='column3item{}'.format(i)))
			main_layout.add_widget(column3)
			#qb_button.text = 'New column added'
		
#		screen_manager.transition.direction = 'right'
#		screen_manager.current = 'resscreen'
#screenManager = ScreenManager()
#screenManager.add_widget(QueryBuilderScreen())
#screenManager.add_widget(ResultScreen(name='results'))
class QBApp(App):
	def build(self):
		return QueryBuilderScreen()
		#return screenManager

if __name__ == '__main__':
	QBApp().run()

