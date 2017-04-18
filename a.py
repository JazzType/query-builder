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
	driver = GraphDatabase.driver("bolt://localhost", auth = basic_auth("neo4j", "password"))
	session = driver.session()	
	qb_button = ObjectProperty()
	next_button = ObjectProperty()
	screen_manager = ObjectProperty()
	toggleColumn = False
	toggleJumps = False
	video_player = ObjectProperty()
	player_column = BoxLayout()
	times_column = BoxLayout(orientation = 'vertical',size_hint=(0.1, 0.65))
	res_layout = ObjectProperty()

	def events(self,obj):
		getBallProperties=self.session.run("MATCH (p:Ball{start_time:'652.48'}) RETURN keys(p) as keys;")
		for record in getBallProperties:
			print(str(record['keys']))
	
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
		ball = self.session.run("MATCH (b:Ball) WHERE b.start_time = '"+ str(time_tuple[0]) + "' AND b.end_time = '" + str(time_tuple[1]) + "' RETURN b.batsman as batsman, b.bowler as bowler ,b.runs as runs ,b.over as over, b.ball as ball, b.innings as innings")
		event = ball.single()
		players = [event['batsman'], event['bowler']]
		ball = str(event['over']) + "." + str(event['ball'])
		runs = str(event['runs'])
		over = str(event['over'])
		inning = str(event['innings'])
		overs_list = self.session.run("MATCH (b:Ball) WHERE b.over = '" + over + "' and b.innings = '" + inning + "' return b.runs" )
		runs_list = [record['b.runs'].encode('UTF-8') for record in overs_list]
		query = self.session.run("MATCH (b:Ball) WHERE b.over = '" + over + "' and b.innings = '" + inning + "' return b.start_time as start_time")
		ball_times = [str(record['start_time']) for record in query]
		self.insert_players(players,ball,runs,over, runs_list, ball_times)
			
	def get_best_batsmen(self, time_tuple):
		batsmen = self.session.run('MATCH (n) WHERE EXISTS(n.BestBatsman) RETURN DISTINCT "node" as element, n.BestBatsman AS BestBatsman')
		self.insert_player_data('Batsmen', [str(record['BestBatsman']) for record in batsmen])
			
	def get_best_bowlers(self, time_tuple):
		bowlers = self.session.run('MATCH (n) WHERE EXISTS(n.BestBowler) RETURN DISTINCT "node" as element, n.BestBowler AS BestBowler')
			
		self.insert_player_data('Bowlers',[str(record['BestBowler']) for record in bowlers])
	
	'''def get_event_details(self, time_tuple):
		query = self.session.run("MATCH (b:Ball) WHERE b.start_time = '"+ str(time_tuple[0]) + "' AND b.end_time = '" + str(time_tuple[1]) + "' RETURN b.batsman as batsman, b.bowler as bowler ,b.runs as runs ,b.over as over, b.ball as ball, b.innings as innings")
		event = query.single()
		players = [event['batsman'], event['bowler']]
		ball = str(event['over']) + "." + str(event['ball'])
		self.insert_info(time_tuple, players, ball)
		self.load_clips(players)
	'''
	def get_event_details(self, time_tuple):
		query = self.session.run("MATCH (b:Ball) WHERE b.start_time = '"+ str(time_tuple[0]) + "' AND b.end_time = '" + str(time_tuple[1]) + "' RETURN b.batsman as batsman, b.bowler as bowler ,b.runs as runs ,b.over as over, b.ball as ball, b.innings as innings")
		event = query.single()
		players = [event['batsman'], event['bowler']]
		ball = str(event['over']) + "." + str(event['ball'])
		over = str(event['over'])
		inning = str(event['innings'])
		print(over,inning)
		self.insert_info(time_tuple, players, ball)
		self.load_clips(players)
		
	def load_clips(self, players):
		query = self.session.run("MATCH (b:Ball) WHERE b.batsman = '" + players[0] +  "' AND b.bowler = '" + players[1] + "' AND (b.runs = '4' or b.runs = '6' or b.runs = 'OUT') return b.start_time as start_time, b.runs as runs")
		#times = [str(record['start_time']) for record in query]
		#runs = [str(record['runs']) for record in query]
		times = []
		runs = []
		for record in query:
			times.append(str(record['start_time']))
			runs.append(str(record['runs']))
		self.insert_clips(players, runs, times)
		
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
		
	def insert_players(self, player_list, ball, runs, over, runs_list, ball_times):		
		#if type(self.player_column) is BoxLayout:
		self.player_column.clear_widgets()	
		over_layout = BoxLayout(orientation='horizontal')		
		x = 0
		for i in ball_times:
			button = Button(text = str(runs_list[x]), size_hint =(0.75,0.15))
			over_layout.add_widget(button)
			button.bind(on_press = lambda x,i=i : self.play_to_pos(i))
			x = x + 1
		self.player_column.add_widget(Button())
		self.player_column.add_widget(Label(text='Batsman: ' + str(player_list[0]), color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text='Bowler: ' + str(player_list[1]), color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text='Over: ' + ball, color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text='Runs: ' + runs, color=(0, 0, 0, 1)))
		self.player_column.add_widget(Label(text = "This Over:", color=(0, 0, 0, 1)))
		self.player_column.add_widget(over_layout)
		#if not self.toggleColumn:
		#	self.main_layout.add_widget(self.player_column)				
		#	self.toggleColumn = True
		
	def insert_player_data(self, player_type, player_list):
		stats_column = BoxLayout(orientation = "vertical")
		stats_column.add_widget(Label(text = player_type + " of the Match", color=(0, 0, 0, 1)))
		stats_column.add_widget(Label(text = "Best " + player_type + " for RCB : " + player_list[0], color=(0, 0, 0, 1)))
		stats_column.add_widget(Label(text = "Best " + player_type +" for CSK : " + player_list[1], color=(0, 0, 0, 1)))
		self.res_layout.add_widget(stats_column)
		
	def insert_info(self, time_tuple, players, ball):
		info_column = BoxLayout(orientation = "vertical")
		info_column.add_widget(Label(text = "Over : " + ball, size_hint=(1, 0.25), color=(0, 0, 0, 1)))
		info_column.add_widget(Label(text = "Batsman : " + players[0] + " - Bowler : " + players[1], size_hint=(1, 0.30), color=(0, 0, 0, 1)))
		info_column.add_widget(Label(text = "Event Timestamps : "  + str(time_tuple[0]) + " - " + str(time_tuple[1]), size_hint=(1, 0.30), color=(0, 0, 0, 1)))
		backBtn = Button(text='Go Back', size_hint=(1, 0.05))
		backBtn.bind(on_press=self.toQueryBuilder)
		info_column.add_widget(backBtn)
		eventBtn = Button(text='Events build', size_hint=(1, 0.05))
		eventBtn.bind(on_press=self.events)
		info_column.add_widget(eventBtn)
		self.res_layout.add_widget(info_column)
		
		#self.res_layout.add_widget(info_column)
			
	def insert_clips(self, players, runs, times):
		print(runs)
		if type(self.times_column) is BoxLayout:
			self.times_column.clear_widgets()
		self.times_column.add_widget(Label(text = players[0] + " vs " + players[1]))
		x = 0
		if not len(times):
			self.times_column.add_widget(Label(text = "No Highlights Found"))
		for i in times:
			button = Button(text = str(runs[x]), size_hint =(1,1))
			self.times_column.add_widget(button)
			button.bind(on_press = lambda x,i=i : self.play_to_pos(i))	
			x = x + 1
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