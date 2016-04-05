## @package Cocopan
# Workflow engine built on top of MongoDB.

from pymongo import MongoClient
from graphviz import Digraph

from datetime import datetime


f = Digraph('finite_state_machine', filename='fsm.gv')
f.body.extend(['rankdir=LR', 'size="8,5"'])
f.attr('node', shape='circle')



## Workflow transitions
class Transition:

	#The next state (_id) (right hand side)
	_end = None

	#Triggers that are used in the combinations. Tuples in the form key=>bool
	_triggers = {}

	#Conditional combinations of triggers that will activate the transition
	#   Combination in the form [trigger key 1, trigger key 2, ..., trigger key n]
	_conditions = []

	## Class constructor
	# @param self The object pointer
	# @param State The starting state
	# @param State The ending state
	def __init__(self, end_state = None, transition_dict=None):
		if end_state != None:
			self._end = end_state.get_state_id()
			self._transitions = {}
			self._conditions = []
		else:
			#Set the end state
			self._end = transition_dict["end"]
			#Set the triggers
			self._triggers = transition_dict["triggers"]
			#Set the conditions
			self._conditons = transition_dict["conditions"]

	## Get the end state
	# @param self The object pointer
	def get_end(self):
		return self._end

	## Set the trigger list
	# @param self The object pointer
	# @param list The trigger list
	def set_triggers(self, triggers):
		self._triggers = triggers

	## Create a new transition trigger
	# @param self The object pointer
	# @param string Unique trigger key
	def trigger_add(self, key):
		# Add the trigger to the dictionary and make it false
		self._triggers[key] = False

	## Remove a transition trigger
	# @param self The object pointer
	# @param string The trigger key
	def trigger_remove(self, key):
		#Delete the trigger from the dictionary
		del self._triggers[key]

	## Activate a trigger
	# @param self The object pointer
	# @param string The trigger key
	def trigger_activate(self, key):
		#Set the trigger to true
		self._triggers[key] = True

	## Get the status of a trigger
	# @param self The object pointer
	# @param string The trigger key
	# @return bool The trigger status (activated or not)
	def trigger_status(self, key):
		return self._triggers[key]

	## Create a new combination of triggers that will activate the transition
	# @param self The object pointer
	# @param list List of trigger keys to create the combinations
	def condition_add(self, trigger_list):
		# Add the trigger list to the combinations
		self._conditions.append(trigger_list)

	## Remove a trigger combination
	# @param self The object pointer
	# @param int The index of the condition to remove
	def condition_remove(self, index):
		del self._conditions[index]

	## Get the conditions list
	# @param self The object pointer
	def get_conditions(self):
		return self._conditions

	## Set the conditions list
	# @param self The object pointer
	# @param list The conditions list
	def set_conditions(self, conditions):
		self._conditions = conditions

	## Check to see if the transition should activate
	# @param self The object pointer
	# @return bool True/False if transition should activate
	def isActivated(self):
		# Iterate over all conditional combinations
		for condition in self._conditions:
			# Number of triggers that are true in the combination
			num_true = 0
			for trigger in condition:
				#If the trigger is activated, increment the number of activated triggers
				if self._triggers[trigger] == True:
					num_true = num_true + 1
			#If the number of activated triggers matches the number of triggers in combination, transition is activated
			if num_true == len(condition):
				return True

		#None of the combinations were complete
		return False

	## Convert the transition object to a dictionary for MongoDB
	# @param self The object pointer
	# @return dict Dictionary representing the transition
	def to_dictionary(self):
		#The return variable
		transition_dict = {}
		#Set the end state
		transition_dict["end"] = self._end
		#Set the triggers
		transition_dict["triggers"] = self._triggers
		#Set the conditions
		transition_dict["conditions"] = self._conditions
		#Return the dictionary
		return transition_dict

	## Convert a transition dictionary to a transition object
	# @param self The object pointer
	# @param dict The transition dictionary
	def from_dictionary(self, transition_dict):
		#Set the end state
		self._end = transition_dict["end"]
		#Set the triggers
		self._triggers = transition_dict["triggers"]
		#Set the conditions
		self._conditons = transition_dict["conditions"]

## Workflow states
class State:

	#The dictionary that holds the MongoDB document representing the state
	_document = {}

	#The MongoDB document _id of the state object
	_doc_id = 0

	#State transitions
	_transitions = {}

	## Class Constructor
	# @param dict MongoDB document as a dictionary
	# @return None
	def __init__(self, doc):
		#Set the MongoDB document
		self._document = doc
		#Set the MongoDB document _id
		self._doc_id = doc['_id']
		self._transitions = {}

    ## Get the State's document _id
    # @param self The object pointer
    # @return string The document _id
	def get_state_id(self):
		return self._document['_id']

	## Set the friendly name of the state
	# @param self The object pointer
	# @param string The name for the state
	def set_name(self, name):
		self._document['description'] = name
		
	## Get field from state
    # @param string Key 
    # @return Value at key
	def get_field(self, key):
		return self._document[key]


	## Get transitions
	# @param self The object pointer
	# @return Dict of transitions
	def get_transitions(self):
		return self._transitions

    ## Add transition
    # @param self The object pointer
    # @param State The transition to be added
    # @return Transition The created transition
	def add_transition(self, end_state):

		#Create a new transition object
		state_transition = Transition(end_state)
		#Add the transition to the state
		self._transitions.update({end_state.get_state_id(): state_transition})
		#Return a pointer to the craeated transition object
		return self._transitions.get(end_state.get_state_id())

	## Remove a transition
	# @param self The object pointer
	# @param State The transition to be removed
	def remove_transition(self, end_state):

		del self._transitions[end_state]

	## Modify a state transition
	# @param self The object pointer
	# @param string The id of the next state
	# @return Transitiion The transition to be modified
	def transition(self, next_state_id):
		return self._transitions.get(next_state_id)



    ## Get the state as a dictionary to persist to MongoDB
    # @param self The object pointer
    # @return dict The State as a dictionary
	def to_dictionary(self):
			#Convert the transitions to dicts and then into an array
			transition_list = []

			for key, trans in self._transitions.items():
				
				transition_list.append(trans.to_dictionary())

				for condition in trans.get_conditions():
					# Workflow visualization simulation using GraphViz
					
					f.edge(str(self.get_state_id()), str(trans.to_dictionary()["end"]), label=str(condition))


			#Replace the transition list in te state dictionary
			self._document["transitions"] = transition_list
    		#Return the state as a dictionary
			return self._document

	## Dictionary to object
	# @param dict Dictionary representation of object from MongoDB
	# @return None
	def from_dictionary(self, dictionary):
		self._document = dictionary
		for transition in self._document["transitions"]:
			#Add the transition to the transitions list
			self._transitions[transition["end"]] = Transition(None, transition)
			self._transitions[transition["end"]].set_conditions(transition["conditions"])
			self._transitions[transition["end"]].set_triggers(transition["triggers"])
			print self._transitions[transition["end"]].get_conditions()



## Workflow objects (objects that move from state to state)
class Object: 

	## Dictionary representing the object (Dictionary format used by MongoDB document)
	_document = {}

    #The MongoDB document _id of the object
	_doc_id = None

	# The current state of the item
	_state = None

    ## Class constructor. Pass in initial state. 
    # @param string State (_id of state) 
    # @return None
	def __init__(self, state=None):
   		self._state = state
   		if state != None:
   			self.set_field("init_state", state.get_state_id())

    ## Get field from object
    # @param string Key 
    # @return Value at key
	def get_field(self, key):
		return self._document[key]

    ## Set field in object
    # @param self The object pointer
    # @param string Key
    # @param Value
	def set_field(self, key, value):
		self._document[key] = value

    ## Object to dictionary
    # @return dict Dictionary representation of object for MongoDB
	def to_dictionary(self):
		return self._document

    ## Dictionary to object
    # @param dict Dictionary representation of object from MongoDB
    # @return None
	def from_dictionary(self, dictionary):
		self._document = dictionary


## Database interface to MongoDB
class Database:

	## MongoDB connection parameters
	_connection_params = None
	

	## Class constructor
	# @param self The object pointer
	# @param string Database connection paramters
	def __init__(self, connection=None):
		self._connection_params = connection
	
	## Connect to the database
	# @param self The object pointer
	# @param string The database name
	# @return MongoClient MongoDB connection instance 
	def connect(self, db_name):
		conn = MongoClient(self._connection_params)[db_name]
		return conn

## Workflow data model
class Workflow:

	## Dictionary representing the object (Dictionary format used by MongoDB document)
	_document = {}

    ## The MongoDB document _id of the object
	_doc_id = None

	## Class constructor
	# @param self The object pointer
	# @param dict The document from MongoDB
	# @return None
	def __init__(self, doc={}):
		self._document = doc
		self._states = []
		self._objects = []
		self._doc_id = None

    ## Dictionary to object
    # @param dict Dictionary representation of object from MongoDB
    # @return None
	def from_dictionary(self, dictionary):
		self._document = dictionary

	## Get the _id of the workflow
	# @param self The object pointer
	# @return string The _id of the workflow
	def get_id(self):
		return self._document["_id"]

	## Get a list of the states that are associated with the workflow
	# @param self The object pointer
	# @return list List of state doc _ids associated with the workflow
	def get_states(self):
		return self._document["states"]

	## Get a list of the objects that are associated with the workflow
	# @param self The object pointer
	# @return list List of object doc _ids associated with the workflow
	def get_objects(self):
		return self._document["objects"]

	## Set the states list
	# @param self The object pointer
	# @param list List of states to save
	def set_states(self, states_list):
		self._document["states"] = states_list

	## Set the objects list
	# @param self The object pointer
	# @param list List of objects to save
	def set_objects(self, objects_list):
		self._document["objects"] = objects_list	

	## Get the dictionary representing the workflow
	# @param self The object pointer
	# @return dict A dictionary representing the workflow
	def to_dictionary(self):
		return self._document


## Workflow engine
class Cocopan:

	## MongoDB database instance
	db = None

	## The MongoDB database name
	_db_name = None

	## The collection that holds the workflows for each process
	_workflow_collection = None

	## The workflow data model representing the Cocopan process
	_workflow_dm = None

	# In memory dict of states
	_states = {}

	## The collection that holds all of the states in the system
	_states_collection = None

	# In memory dicts of objects
	_objects = {}

	## The collection that holds all of the objects in the system
	_objects_collection = None

	## Class constructor
	# @param string MongoDB connection parameters
	def __init__(self, connection=None):
		#Initialize the connection to the MongoDB instance
		self.db = Database(connection)
		#Initialize the workflow data model 
		self._workflow_dm = Workflow()


	# Helper function to laod state
	def _load_state(self, state_id):
			# Get a connection instance to MongoDB
			conn = self.db.connect(self._db_name)
			# Get an instance of the states collection in MongoDB
			state_collection = conn[self._states_collection]
			# Get the state from mongoDB as a dictionary
			doc_dict = conn[self._states_collection].find_one({"_id": state_id})

    		# Create a new in memory state object from the dictionary
			self._states[state_id] = State(doc_dict)
			self._states[state_id].from_dictionary(doc_dict)

	# Helper function to load object
	def _load_object(self, object_id):
			# Get a connection instance to MongoDB
			conn = self.db.connect(self._db_name)
			# Get an instance of the objects collection in MongoDB
			object_collection = conn[self._objects_collection]
			# Get the object from mongoDB as a dictionary
			doc_dict = conn[self._objects_collection].find_one({"_id": object_id})

    		# Create a new in memory object from the dictionary
			self._objects[object_id] = Object()
			self._objects[object_id].from_dictionary(doc_dict)

	## Load existing workflow from MongoDB
	# @param self The object pointer
	# @param string The workflow identifier
	def load(self, workflow_id):

		#Check to see if the workflow exists
		# Get a connection instance to MongoDB
		conn = self.db.connect(self._db_name)
		# A workflow exists with that identifier
		if conn[self._workflow_collection].find({"_id": workflow_id}).limit(1).count() > 0:
			print "WORKFLOW EXISTS"
			#Get the document as a dictionary
			doc_dict = conn[self._workflow_collection].find_one({"_id": workflow_id})
			#Create the workflow data model object
			self._workflow_dm = Workflow(doc_dict)
			#Get a list of states associated with the workflow
			states_list = self._workflow_dm.get_states()

			#Load each state into memory
			for state in states_list:
				self._load_state(state)

			#Get a list of objects associated with the workflow
			objects_list = self._workflow_dm.get_objects()

			#Load each object into memory
			for it_object in objects_list:
				self._load_object(it_object)

			return True
		# A workflow does not exist with that identifier
		else:
			print "WORKFLOW DOES NOT EXIST"
			# Get an instance of the workflow collection in MongoDB
			workflow_collection = conn[self._workflow_collection]
			#Create a blank document in the workflow collection and get the document ID back
			result = workflow_collection.insert_one({"_id": workflow_id})
			#Get the _id of the document
			doc_id = result.inserted_id
			#Get the document as a dictionary
			doc_dict = conn[self._workflow_collection].find_one({"_id": workflow_id})
			#Create the workflow data model object
			self._workflow_dm = Workflow(doc_dict)

			return False

	## Set the MongoDB database name
	# @param string MongoDB database name
	def set_db_name(self, database):
		self._db_name = database

	## Set the MongoDB collection that holds the states
	# @param string Collection name that holds the states
	def set_state_collection(self, collection):
		self._states_collection = collection 

	## Set the MongoDB collection that holds the objects
	# @param string Collection name that holds the objects
	def set_object_collection(self, collection):
		self._objects_collection = collection 

	## Set the MongoDB collection that holds the workflow documents
	# @param string Collection name that holds the workflows
	def set_workflow_collection(self, collection):
		self._workflow_collection = collection 	

	## Create a new workflow state
	# @param self The object pointer
	# @param string A unique identifier for the state
	# @return State Return the created state
	def new_state(self, state_id):
		# Get a connection instance to MongoDB
		conn = self.db.connect(self._db_name)
		# Get an instance of the states collection in MongoDB
		state_collection = conn[self._states_collection]
		#Create a blank document in the states collection and get the document ID back
		result = state_collection.insert_one({"_id": state_id})
		#Get the _id of the document
		doc_id = result.inserted_id
		#Get the document as a dictionary
		doc_dict = conn[self._states_collection].find_one({"_id": doc_id})
		#Create a new state object
		state = State(doc_dict)
		#Add the state object to the in memory list of states
		self._states[doc_id] = state
		#Return the created state object
		return self._states.get(doc_id)

	## Retrive a state from the workflow
	# @param self The object pointer
	# @param string The _id of the state (MondoDB ID)
	# @return State The State object
	def get_state(self, state_id):
		#See if the state is in memory
		try:
			return self._states[state_id]
    	#If not, retrive from MongoDB (lazy loading of states)
		except KeyError:
			# Get a connection instance to MongoDB
			conn = self.db.connect(self._db_name)
			# Get an instance of the states collection in MongoDB
			state_collection = conn[self._states_collection]
			# Get the state from mongoDB as a dictionary
    		doc_dict = conn[self._states_collection].find_one({"_id": state_id})
    		# Create a new in memory state object from the dictionary
    		self._states[state_id] = State(doc_dict)

	## Create the object that will be tracked through the workflow
	# @param self The object pointer
	# @param string The ID of the start state
	# @return Object Return the created object
	def new_object(self, start_state):
		# Get a connection instance to MongoDB
		conn = self.db.connect(self._db_name)
		# Get an instance of the objects collection in MongoDB
		object_collection = conn[self._objects_collection]
		#Create a blank document in the objects collection and get the document ID back
		result = object_collection.insert_one({})
		#Get the _id of the document
		doc_id = result.inserted_id
		#Get the document as a dictionary
		doc_dict = conn[self._objects_collection].find_one({"_id": doc_id})
		#Create the new object
		created_object = Object(start_state)
		#Add the state object to the in memory list of states
		self._objects[doc_id] = created_object
		#Return the created state object
		return created_object


	#Helper function to save states
	def _save_states(self):
		for _id, it_state in self._states.items():
			#Temporary variable to hold dictinary representation
			temp_dict = it_state.to_dictionary()
			#Replace the document in mongo with the new state
			conn = self.db.connect(self._db_name)
			state_collection = conn[self._states_collection]
			state_collection.replace_one({"_id" : _id}, temp_dict)

	#Helper function to save objects
	def _save_objects(self):
		for _id, it_object in self._objects.items():
			#Temporary variable to hold dictinary representation
			temp_dict = it_object.to_dictionary()
			#Replace the document in mongo with the new object
			conn = self.db.connect(self._db_name)
			object_collection = conn[self._objects_collection]
			object_collection.replace_one({"_id" : _id}, temp_dict)

	#Helper function to save the workflow
	def _save_workflow(self):
		#Temporary list to hold the _ids of the states associated with the workflow
		temp_list = []
		#Iterate and the _ids from each state in memory to the temp list
		for _id, it_state in self._states.items():
			temp_list.append(_id)
		#Set the workflow states to the temporary list (from in memory states)
		self._workflow_dm.set_states(temp_list)

		#Temporary list to hold the _ids of the objects associated with the workflow
		temp_list = []
		#Iterate and the _ids from each object in memory to the temp list
		for _id, it_object in self._objects.items():
			temp_list.append(_id)
		#Set the workflow objects to the temporary list (from in memory objects)
		self._workflow_dm.set_objects(temp_list)

		#Replace the document in mongo with the new workflow
		conn = self.db.connect(self._db_name)
		workflow_collection = conn[self._workflow_collection]
		workflow_collection.replace_one({"_id" : self._workflow_dm.get_id()}, self._workflow_dm.to_dictionary())

	## Persist changes to Mongo
	# @param self The object pointer
	def save(self):
		#Save the states
		self._save_states()
		#Save the objects
		self._save_objects()
		#Save the workflow
		self._save_workflow()

	## Visualize the workflow using Graphviz
	# @param self The object pointer
	# @return None
	def visualize_it(self): #I'll give you somethin' to do
		f = Digraph('finite_state_machine', filename='fsm.gv')
		f.body.extend(['rankdir=LR', 'size="8,5"'])
		f.attr('node', shape='circle')
		#Iterate through each state
		for key, state in self._states.items():
			#Create a node for each state
			f.node(str(state.get_state_id()), label=state.get_field("description"))
			
			#Iterate over each transition in the state
			if state != None:
				for key, trans in state.get_transitions().items():
					if trans != None:
						print trans.get_end()
						for condition in trans.get_conditions():
							f.edge(str(state.get_state_id()), str(trans.to_dictionary()["end"]), label=str(condition))
		f.view()



workflow = Cocopan()
workflow.set_db_name("test10")
workflow.set_state_collection("states")
workflow.set_object_collection("objects")
workflow.set_workflow_collection("workflowss")
if workflow.load("test_test8"):
	#workflow.get_state("m1").remove_transition("m2")
	workflow.get_state("m1").transition("m2").condition_remove(1)
	workflow.get_state("m1").transition("m2").condition_remove(0)
	workflow.visualize_it()
	#workflow.save()
else:
	#M1 state
	state1 = workflow.new_state("m1")
	state1.set_name("M1")
	#M2 state
	state2 = workflow.new_state("m2")
	state2.set_name("M2")
	#M3 state
	state3 = workflow.new_state("m3")
	state3.set_name("M3")
	#M4 state
	state4 = workflow.new_state("m4")
	state4.set_name("M4")
	#M5 state
	state5 = workflow.new_state("m5")
	state5.set_name("M5")

	workflow.new_object(state1)

	#Create a new transition from state1 to state 2
	state1.add_transition(state2)

	state1.transition(state2).trigger_add("signature_advisor")
	state1.transition(state2).trigger_add("signature_dean")

	state1.transition(state2).condition_add(["signature_advisor", "signature_dean"])

	#Create a new transition from state 2 to state 3
	state2.add_transition(state3)

	state2.transition(state3).trigger_add("test_completed")
	state2.transition(state3).trigger_add("test_grade_accepted")
	state2.transition(state3).condition_add(["test_completed", "test_grade_accepted"])

	state2.transition(state3).trigger_add("test_exmempted")
	state2.transition(state3).condition_add(["test_exempted"])

	#Create a new fork transition from 3 to 4 or 5
	state3.add_transition(state4)
	state3.add_transition(state5)

	state3.transition(state4).trigger_add("assessment_soft_skills_complete")
	state3.transition(state4).trigger_add("advisor_signature")
	state3.transition(state4).trigger_add("system_override")
	state3.transition(state4).condition_add(["assessment_soft_skills_complete", "assessment_soft_skills_complete"])
	state3.transition(state4).condition_add(["system_override"])

	state3.transition(state5).trigger_add("career_change_decision")
	state3.transition(state5).trigger_add("advisor_signature")
	state3.transition(state5).trigger_add("dean_signature")
	state3.transition(state5).trigger_add("system_override")
	state3.transition(state5).condition_add(["career_change_decision", "advisor_signature", "dean_signature"])
	state3.transition(state5).condition_add(["system_override"])



	#Should the student move on?
	print state1.transition(state2).isActivated()

	#Create a new object in the workflow
	#workflow.new_object(state1.get_state_id())

	workflow.save()
























