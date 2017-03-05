import kivy
import numpy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition
from neo4j.v1 import GraphDatabase, basic_auth

class QueryBuilder(BoxLayout):
	qb_button = ObjectProperty()
	screen_manager = ObjectProperty()
	toggleColumn = False
	video_player = ObjectProperty()
	player_column = BoxLayout(orientation='vertical', size_hint=(0.1, 1))
	def update_button(self, main_layout):
		Neo4jInterface().init(11697.0, main_layout)

	def change_screen(self, screen_name):		
		#self.screen_manager.current = screen_name
		pass
	def insert_players(self, player_list, main_layout):		
		if type(self.player_column) is BoxLayout:
				self.player_column.clear_widgets()						
		self.player_column.add_widget(Label(text='Batsman: ' + str(player_list[0][0])))
		self.player_column.add_widget(Label(text='Bowler: ' + str(player_list[0][1])))
		if not self.toggleColumn:
			main_layout.add_widget(self.player_column)			
			self.toggleColumn = True
		
class QBApp(App):
	def build(self):
		return QueryBuilder()		

class Neo4jInterface():
	driver = GraphDatabase.driver("bolt://localhost:7687", auth = basic_auth("neo4j", "password"))
	session = driver.session()
	QueryBuilderObject = QueryBuilder()
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

	def populate_objects(self, time_tuple, main_layout):
		ball = self.session.run("MATCH (n {start_time: '" + str(time_tuple[0]) + "', end_time:'" + str(time_tuple[1]) + "'}) RETURN DISTINCT 'node' as element, n.over as over, n.innings as innings, n.batsman as batsman, n.bowler as bowler UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.end_time) RETURN DISTINCT 'relationship' AS element, r.over as over, r.innings as innings, r.batsman as batsman, r.bowler as bowler")

		self.QueryBuilderObject.insert_players([(str(record['batsman']), str(record['bowler'])) for record in ball], main_layout)		

	def init(self, pause_time, main_layout):
		end_times = self.session.run("MATCH (n) WHERE EXISTS(n.end_time) RETURN DISTINCT 'node' as element, n.end_time AS end_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.end_time) RETURN DISTINCT 'relationship' AS element, r.end_time AS end_time")
		end_times = [float(record['end_time']) for record in end_times]
		start_times = self.session.run("MATCH (n) WHERE EXISTS(n.start_time) RETURN DISTINCT 'node' as element, n.start_time AS start_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.start_time) RETURN DISTINCT 'relationship' AS element, r.start_time AS start_time")
		start_times = [float(record['start_time']) for record in start_times]
		tuple_array = [(start_time, end_time) for start_time, end_time in zip(start_times, end_times)]				
		self.populate_objects(tuple_array[self.binary_search(tuple_array, pause_time)], main_layout)


if __name__ == '__main__':
	QBApp().run()
