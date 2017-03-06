import kivy
import time
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
	next_button = ObjectProperty()
	screen_manager = ObjectProperty()
	toggleColumn = False
	video_player = ObjectProperty()
	player_column = BoxLayout(orientation='vertical', size_hint=(0.1, 1))
	res_layout = ObjectProperty()
	

	def update_button(self, main_layout, res_layout):
		Neo4jInterface().init(self.video_player.position, main_layout, res_layout)

	def change_screen(self, screen_name):		
		self.screen_manager.current = screen_name
		
	def insert_players(self, player_list, main_layout):		
		if type(self.player_column) is BoxLayout:
				self.player_column.clear_widgets()						
		self.player_column.add_widget(Label(text='Batsman: ' + str(player_list[0][0])))
		self.player_column.add_widget(Label(text='Bowler: ' + str(player_list[0][1])))
		if not self.toggleColumn:
			main_layout.add_widget(self.player_column)			
			self.toggleColumn = True
		
	def insert_player_data(self, player_type, player_list, res_layout):
		stats_column = BoxLayout(orientation = "vertical")
		stats_column.add_widget(Label(text = player_type + " of the Match"))
		stats_column.add_widget(Label(text = "Best " + player_type + " for RCB : " + player_list[0]))
		stats_column.add_widget(Label(text = "Best " + player_type +" for CSK : " + player_list[1]))
		res_layout.add_widget(stats_column)
		
	def insert_info(self, time_tuple, players, ball, res_layout):
		info_column = BoxLayout(orientation = "vertical")
		info_column.add_widget(Label(text = "Over : " + ball))
		info_column.add_widget(Label(text = "Batsman : " + players[0] + " - Bowler : " + players[1]))
		info_column.add_widget(Label(text = "Event Timestamps : "  + str(time_tuple[0]) + " - " + str(time_tuple[1]) ))
		res_layout.add_widget(info_column)
		
class QBApp(App):
	def build(self):
		return QueryBuilder()		

class Neo4jInterface():
	driver = GraphDatabase.driver("bolt://localhost:7687", auth = basic_auth("neo4j", "aditya"))
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
			
	def get_best_batsmen(self, time_tuple, res_layout):
		batsmen = self.session.run('MATCH (n) WHERE EXISTS(n.BestBatsman) RETURN DISTINCT "node" as element, n.BestBatsman AS BestBatsman LIMIT 25 UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.BestBatsman) RETURN DISTINCT "relationship" AS element, r.BestBatsman AS BestBatsman LIMIT 25')
	
		self.QueryBuilderObject.insert_player_data('Batsmen', [str(record['BestBatsman']) for record in batsmen], res_layout)
			
	def get_best_bowlers(self, time_tuple, res_layout):
		bowlers = self.session.run('MATCH (n) WHERE EXISTS(n.BestBowler) RETURN DISTINCT "node" as element, n.BestBowler AS BestBowler LIMIT 25 UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.BestBowler) RETURN DISTINCT "relationship" AS element, r.BestBowler AS BestBowler LIMIT 25')
			
		self.QueryBuilderObject.insert_player_data('Bowlers',[str(record['BestBowler']) for record in bowlers], res_layout)
	
	def get_event_details(self, time_tuple, res_layout):
		query = self.session.run("MATCH (b:Ball) WHERE b.start_time = '"+ str(time_tuple[0]) + "' AND b.end_time = '" + str(time_tuple[1]) + "' RETURN b.batsman as batsman, b.bowler as bowler ,b.runs as runs ,b.over as over, b.ball as ball")
		event = query.single()
		players = [event['batsman'], event['bowler']]
		ball = str(event['over']) + "." + str(event['ball'])
		
		self.QueryBuilderObject.insert_info(time_tuple, players, ball , res_layout)
	
	def init(self, pause_time, main_layout, res_layout):
		res_layout.clear_widgets()
		end_times = self.session.run("MATCH (n) WHERE EXISTS(n.end_time) RETURN DISTINCT 'node' as element, n.end_time AS end_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.end_time) RETURN DISTINCT 'relationship' AS element, r.end_time AS end_time")
		end_times = [float(record['end_time']) for record in end_times]
		start_times = self.session.run("MATCH (n) WHERE EXISTS(n.start_time) RETURN DISTINCT 'node' as element, n.start_time AS start_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.start_time) RETURN DISTINCT 'relationship' AS element, r.start_time AS start_time")
		start_times = [float(record['start_time']) for record in start_times]
		tuple_array = [(start_time, end_time) for start_time, end_time in zip(start_times, end_times)]	
		time_tuple = tuple_array[self.binary_search(tuple_array, pause_time)]
		self.populate_objects(time_tuple, main_layout)
		self.get_event_details(time_tuple, res_layout)
		self.get_best_batsmen(time_tuple, res_layout)
		self.get_best_bowlers(time_tuple, res_layout)
		
if __name__ == '__main__':
	QBApp().run()
