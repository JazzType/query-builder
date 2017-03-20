import kivy
import time
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from neo4j.v1 import GraphDatabase, basic_auth
from kivy.cache import Cache
from kivy.atlas import Atlas
from kivy.graphics.instructions import Canvas
from kivy.graphics.context_instructions import Color
from kivy.graphics import Rectangle


class QueryBuilder(BoxLayout):
	driver = GraphDatabase.driver("bolt://localhost:7687", auth = basic_auth("neo4j", "password"))
	session = driver.session()	
	qb_button = ObjectProperty()
	next_button = ObjectProperty()
	screen_manager = ObjectProperty()
	toggleColumn = False
	toggleJumps = False
	video_player = ObjectProperty()
	player_column = ObjectProperty()
	times_column = BoxLayout(orientation = 'vertical',size_hint=(0.1, 0.65))
	res_layout = ObjectProperty()	
	

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

	def populate_objects(self, time_tuple):
		ball = self.session.run("MATCH (b:Ball) WHERE b.start_time = '"+ str(time_tuple[0]) + "' AND b.end_time = '" + str(time_tuple[1]) + "' RETURN b.batsman as batsman, b.bowler as bowler ,b.runs as runs ,b.over as over, b.ball as ball")
		event = ball.single()
		players = [event['batsman'], event['bowler']]
		ball = str(event['over']) + "." + str(event['ball'])
		runs = str(event['runs'])
		self.insert_players(players,ball,runs)
			
	def get_best_batsmen(self, time_tuple):
		batsmen = self.session.run('MATCH (n) WHERE EXISTS(n.BestBatsman) RETURN DISTINCT "node" as element, n.BestBatsman AS BestBatsman LIMIT 25 UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.BestBatsman) RETURN DISTINCT "relationship" AS element, r.BestBatsman AS BestBatsman LIMIT 25')
	
		self.insert_player_data('Batsmen', [str(record['BestBatsman']) for record in batsmen])
			
	def get_best_bowlers(self, time_tuple):
		bowlers = self.session.run('MATCH (n) WHERE EXISTS(n.BestBowler) RETURN DISTINCT "node" as element, n.BestBowler AS BestBowler LIMIT 25 UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.BestBowler) RETURN DISTINCT "relationship" AS element, r.BestBowler AS BestBowler LIMIT 25')
			
		self.insert_player_data('Bowlers',[str(record['BestBowler']) for record in bowlers])
	
	def get_event_details(self, time_tuple):
		query = self.session.run("MATCH (b:Ball) WHERE b.start_time = '"+ str(time_tuple[0]) + "' AND b.end_time = '" + str(time_tuple[1]) + "' RETURN b.batsman as batsman, b.bowler as bowler ,b.runs as runs ,b.over as over, b.ball as ball")
		event = query.single()
		players = [event['batsman'], event['bowler']]
		ball = str(event['over']) + "." + str(event['ball'])
		self.insert_info(time_tuple, players, ball)
		self.load_clips(players)
	
	def load_clips(self, players):
		query = self.session.run("MATCH (b:Ball) WHERE b.batsman = '" + players[0] +  "' AND b.bowler = '" + players[1] + "' AND b.runs = '4' return b.start_time as start_time")
		good_times = [str(record['start_time']) for record in query]
		self.insert_clips(good_times)
		
	def init(self, pause_time):
		self.res_layout.clear_widgets()
		end_times = self.session.run("MATCH (n) WHERE EXISTS(n.end_time) RETURN DISTINCT 'node' as element, n.end_time AS end_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.end_time) RETURN DISTINCT 'relationship' AS element, r.end_time AS end_time")
		end_times = [float(record['end_time']) for record in end_times]
		start_times = self.session.run("MATCH (n) WHERE EXISTS(n.start_time) RETURN DISTINCT 'node' as element, n.start_time AS start_time UNION ALL MATCH ()-[r]-() WHERE EXISTS(r.start_time) RETURN DISTINCT 'relationship' AS element, r.start_time AS start_time")
		start_times = [float(record['start_time']) for record in start_times]
		tuple_array = [(start_time, end_time) for start_time, end_time in zip(start_times, end_times)]	
		time_tuple = tuple_array[self.binary_search(tuple_array, pause_time)]
		self.populate_objects(time_tuple)
		self.get_event_details(time_tuple)
		self.get_best_batsmen(time_tuple)
		self.get_best_bowlers(time_tuple)

	def update_button(self):
		self.video_player.state = 'pause'
		self.init(self.video_player.position)

	def change_screen(self, screen_name):		
		self.screen_manager.current = screen_name
		
	def insert_players(self, player_list, ball, runs):		
		#if type(self.player_column) is BoxLayout:
		self.player_column.clear_widgets()						
		self.player_column.add_widget(Label(text='Batsman: ' + str(player_list[0]), color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text='Bowler: ' + str(player_list[1]), color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text='Over: ' + ball, color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text='Runs: ' + runs, color=(0, 0, 0, 1)))
		#if not self.toggleColumn:
		#	self.main_layout.add_widget(self.player_column, len(self.main_layout.children))			
		#	self.toggleColumn = True
		
	def insert_player_data(self, player_type, player_list):
		stats_column = BoxLayout(orientation = "vertical")
		stats_column.add_widget(Label(text = player_type + " of the Match", color=(0, 0, 0, 1)))
		stats_column.add_widget(Label(text = "Best " + player_type + " for RCB : " + player_list[0], color=(0, 0, 0, 1)))
		stats_column.add_widget(Label(text = "Best " + player_type +" for CSK : " + player_list[1], color=(0, 0, 0, 1)))
		self.res_layout.add_widget(widget=stats_column)
		
	def insert_info(self, time_tuple, players, ball):
		info_column = BoxLayout(orientation = "vertical")
		info_column.add_widget(Label(text = "Over : " + ball, size_hint=(1, 0.25), color=(0, 0, 0, 1)))
		info_column.add_widget(Label(text = "Batsman : " + players[0] + " - Bowler : " + players[1], size_hint=(1, 0.30), color=(0, 0, 0, 1)))
		info_column.add_widget(Label(text = "Event Timestamps : "  + str(time_tuple[0]) + " - " + str(time_tuple[1]), size_hint=(1, 0.30), color=(0, 0, 0, 1)))
		backBtn = Button(text='Go Back', size_hint=(1, 0.05))
		backBtn.bind(on_press=self.toQueryBuilder)
		info_column.add_widget(backBtn)
		self.res_layout.add_widget(info_column)
			
	def insert_clips(self, times):
		print(times)
		if type(self.times_column) is BoxLayout:
			self.times_column.clear_widgets()
		y_hint = 1/len(times)
		for i in times:
			button = Button(text = "Jump to : " + i, size_hint =(1,y_hint))
			self.times_column.add_widget(button)
			button.bind(on_press = lambda x,i=i : self.play_to_pos(i))
		if not self.toggleJumps:
			self.main_layout.add_widget(self.times_column)			
			self.toggleJumps = True
	
	def play_to_pos(self, time):
		print (time)
		self.video_player.seek(float(time)/self.video_player.duration)
		self.video_player.state = 'play'	
		
	def toQueryBuilder(self, obj):
		self.change_screen('QueryBuilderScreen')
class QBApp(App):
	def build(self):
		atlas = Atlas("assets/material.atlas")
		Cache.append("kv.atlas", 'data/images/defaulttheme', atlas)		
		return QueryBuilder()		

		
if __name__ == '__main__':
	QBApp().run()
