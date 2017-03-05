import kivy
import numpy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from neo4j.v1 import GraphDatabase, basic_auth

driver = GraphDatabase.driver("bolt://localhost:7687", auth = basic_auth("neo4j", "aditya"))
session = driver.session()

class QueryBuilder(BoxLayout):
	qb_button = ObjectProperty()
	screen_manager = ObjectProperty()
	toggleColumn = False
	video_player = ObjectProperty()
	def update_button(self, qb_button, main_layout):
		if not self.toggleColumn:
			self.toggleColumn = True
			column3 = BoxLayout(orientation='vertical', size_hint=(0.1, 1))
			for i in range(3):
				column3.add_widget(Label(text='column3item{}'.format(i)))
			main_layout.add_widget(column3)
		Neo4jInterface().init(self.video_player.position)
	def change_screen(self, screen_name):		
		self.screen_manager.current = screen_name
			

	
		
class QBApp(App):
	def build(self):
		return QueryBuilder()		

class Neo4jInterface():
	def binary_search(self, tuple_array, pause_time):
		low = 0
		high = len(tuple_array)
		previous_index = -2
		mid = int((low+high)/2)
		while high >= low:				
			mid = int((low + high)/2)						
			if tuple_array[mid][0] < pause_time and pause_time < tuple_array[mid][1]: 
				print("Approximate match", tuple_array[mid])				
				return mid
			if tuple_array[mid][0] == pause_time or tuple_array[mid][1] == pause_time:
				print("Exact Match", tuple_array[mid])
				return mid
			if tuple_array[mid][0] < pause_time:
				low = mid+1				
			elif tuple_array[mid][1] > pause_time:
				high = mid-1

		print("Not in any range, returning", tuple_array[mid-1])
		return mid-1

	def init(self, pause_time):
		end_times = session.run("MATCH (n) WHERE EXISTS(n.end_time) RETURN DISTINCT 'node' as element, n.end_time AS end_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.end_time) RETURN DISTINCT 'relationship' AS element, r.end_time AS end_time")
		end_times = [float(record['end_time']) for record in end_times]
		start_times = session.run("MATCH (n) WHERE EXISTS(n.start_time) RETURN DISTINCT 'node' as element, n.start_time AS start_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.start_time) RETURN DISTINCT 'relationship' AS element, r.start_time AS start_time")
		start_times = [float(record['start_time']) for record in start_times]
		tuple_array = [(start_time, end_time) for start_time, end_time in zip(start_times, end_times)]				
		print(self.binary_search(tuple_array, pause_time))

if __name__ == '__main__':
	QBApp().run()
