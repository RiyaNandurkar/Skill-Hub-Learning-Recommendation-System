"""
Recommendation System

Links
	- https://towardsdatascience.com/how-to-build-a-recommendation-engine-quick-and-simple-aec8c71a823e
	- https://www.analyticsvidhya.com/blog/2018/06/comprehensive-guide-recommendation-engine-python/


source_path = os.path.join("data/coursera-courses.csv")
"""

import streamlit as st
import pandas as pd 
import numpy as np
import os
import matplotlib.pyplot as plt 
import altair as alt

from rake_nltk import Rake
from nltk.corpus import stopwords 
from sklearn.metrics.pairwise import cosine_similarity,linear_kernel
from sklearn.feature_extraction.text import CountVectorizer
from PIL import Image

FILTERED_COURSES = None
SELECTED_COURSE = None



video1 = open("student.mp4", "rb") 
img = Image.open("img.png")

@st.cache(persist=True)
def clean_col_names(df, columns):
	"""
	Cleans column names
	-----
	columns:
		List of column names
	"""

	new = []
	for c in columns:
		new.append(c.lower().replace(' ','_'))
	return new

@st.cache(persist=True)
def prepare_data(df):
	"""
	Prepares the final dataset
	-----
	df:
		dataframe
	"""

	# clean column names
	df.columns = clean_col_names(df, df.columns)

	# impute missing values that creeped in
	df['skills'] = df['skills'].fillna('Missing')
	df['instructors'] = df['instructors'].fillna('Missing')

	# making certain features numeric
	def make_numeric(x):
		if(x=='Missing'):
			return np.nan
		return float(x)

	df['course_rating'] = df['course_rating'].apply(make_numeric)
	df['course_rated_by'] = df['course_rated_by'].apply(make_numeric)
	df['percentage_of_new_career_starts'] = df['percentage_of_new_career_starts'].apply(make_numeric)
	df['percentage_of_pay_increase_or_promotion'] = df['percentage_of_pay_increase_or_promotion'].apply(make_numeric)

	def make_count_numeric(x):
	    if('k' in x):
	        return (float(x.replace('k','')) * 1000)
	    elif('m' in x):
	        return (float(x.replace('m','')) * 1000000)
	    elif('Missing' in x):
	        return (np.nan)

	df['enrolled_student_count'] = df['enrolled_student_count'].apply(make_count_numeric)

    # extract time to complete
	def find_time(x):	
	    l = x.split(' ')
	    idx = 0
	    for i in range(len(l)):
	        if(l[i].isdigit()):
	            idx = i 
	    try:
	        return (l[idx] + ' ' + l[idx+1])
	    except:
	        return l[idx]

	df['estimated_time_to_complete'] = df['estimated_time_to_complete'].apply(find_time)

	# split by skills
	def split_it(x):
		return (x.split(','))
	df['skills'] = df['skills'].apply(split_it)

	return df



@st.cache(allow_output_mutation=True)
def load_data():
	source_path1 = os.path.join("data/coursera-courses-overview.csv")
	source_path2 = os.path.join("data/coursera-individual-courses.csv")
	df_overview = pd.read_csv(source_path1)
	df_individual = pd.read_csv(source_path2)
	df = pd.concat([df_overview, df_individual], axis=1)

	# preprocess it now
	df = prepare_data(df)

	return df

@st.cache(persist=True)	
def filter(dataframe, chosen_options, feature, id):
	selected_records = []
	for i in range(1000):
		for op in chosen_options:
			if op in dataframe[feature][i]:
				selected_records.append(dataframe[id][i])
	return selected_records

def extract_keywords(df, feature):
    r = Rake()
    keyword_lists = []
    for i in range(1000):
        descr = df[feature][i]
    
        r.extract_keywords_from_text(descr)		
        key_words_dict_scores = r.get_word_degrees()			
        keywords_string = " ".join(list(key_words_dict_scores.keys()))
        keyword_lists.append(keywords_string)
        
    return keyword_lists

def extract_keywords(df, feature):

    r = Rake()
    keyword_lists = []
    for i in range(df[feature].shape[0]):
        descr = df[feature][i]
        r.extract_keywords_from_text(descr)
        key_words_dict_scores = r.get_word_degrees()
        keywords_string = " ".join(list(key_words_dict_scores.keys()))
        keyword_lists.append(keywords_string)
        
    return keyword_lists

def recommendations(df, input_course, cosine_sim, find_similar=True, how_many=5):
    
    # initialise recommended courses list
    recommended = []
    selected_course = df[df['course_name']==input_course]
    
    # index of the course fed as input
    idx = selected_course.index[0]

    # creating a Series with the similarity scores in descending order
    if(find_similar):
        score_series = pd.Series(cosine_sim[idx]).sort_values(ascending = False)
    else:
        score_series = pd.Series(cosine_sim[idx]).sort_values(ascending = True)

    # getting the indexes of the top 'how_many' courses
    if(len(score_series) < how_many):
    	how_many = len(score_series)
    top_sugg = list(score_series.iloc[1:how_many+1].index)
    
    # populating the list with the titles of the best 10 matching 
    for i in top_sugg:
        qualified = df['course_name'].iloc[i]
        recommended.append(qualified)
        
    return recommended

def content_based_recommendations(df, input_course, courses):

	# filter out the courses
	df = df[df['course_name'].isin(courses)].reset_index()
	# create description keywords
	df['descr_keywords'] = extract_keywords(df, 'description')
	# instantiating and generating the count matrix
	count = CountVectorizer()
	count_matrix = count.fit_transform(df['descr_keywords'])
	# generating the cosine similarity matrix
	cosine_sim = cosine_similarity(count_matrix, count_matrix)
    
	# make the recommendation
	#rec_courses_similar = recommendations(df, input_course, cosine_sim, True)
	#temp_sim = df[df['course_name'].isin(rec_courses_similar)]
	#rec_courses_dissimilar = recommendations(df, input_course, cosine_sim, False)
	#temp_dissim = df[df['course_name'].isin(rec_courses_dissimilar)]

	# top 3
	#st.write("Top 5 most similar courses")
	#st.write(temp_sim)
	#st.write("Top 5 most dissimilar courses")
	#st.write(temp_dissim)


def prep_for_cbr(df):

	# content-based filtering
	#st.header("SkiLL_HuB : Learning Recommendation System")
	
	#st.sidebar.write("Choose courses from 'Select Skills' dropdown menu")

	# filter by skills
	skills_avail = []
	for i in range(1000):
		skills_avail = skills_avail + df['skills'][i]
	skills_avail = list(set(skills_avail))
	skills_select = st.sidebar.multiselect("Select Skills", skills_avail)
	# use button to make the update of filtering
	skill_filtered = None		
	courses = None
	input_course = "Nothing"
	#if st.sidebar.button("Filter Courses"):
	temp = filter(df, skills_select, 'skills', 'course_url')	
	skill_filtered = df[df['course_url'].isin(temp)].reset_index()
	# update filtered courses
	courses = skill_filterediltered['course_name']
	st.write("### Filtered courses based on skill preferences")
	st.write(skill_filtered)
	# some more
	st.write("**Number of programmes filtered:**",skill_filtered.shape[0])
	st.write("**Number of courses:**",
		skill_filtered[skill_filtered['learning_product_type']=='COURSE'].shape[0])
	st.write("**Number of professional degrees:**",
		skill_filtered[skill_filtered['learning_product_type']=='PROFESSIONAL CERTIFICATE'].shape[0])
	st.write("**Number of specializations	:**",
		skill_filtered[skill_filtered['learning_product_type']=='SPECIALIZATION'].shape[0])
	# basic plots
	chart = alt.Chart(skill_filtered).mark_bar().encode(
		y = 'course_provided_by:N',
		x = 'count(course_provided_by):Q'
	).properties(
		title = 'Organizations providing these courses'
	)
	st.altair_chart(chart)

	# there should be more than atleast 2 courses
	if(len(courses)<=2):
		st.write("*There should be atleast 3 courses. Do add more.*")

	input_course = st.sidebar.selectbox("Select Course", courses, key='courses')
	# use button to initiate content-based recommendations
	#else:
		#st.write("```Adjust the 'Select Skills' filter on the sidebar```")

	#rec_radio = st.sidebar.radio("Recommend Similar Courses", ('no', 'yes'), index=0)
	#if (rec_radio=='yes'):
	#	content_based_recommendations(df, input_course, courses)

	# recommend based on selected course



def main():

	st.title("SkiLL_HuB : Learning Recommendation System")

	menu = ["Home","Recommend","About"]
	choice = st.sidebar.selectbox("MENU",menu)

	df = load_data()

	if choice == "Home":
		
		st.video(video1)
		st.write(" ")
		st.write(" ")
		st.write(" ")
#st.video(video1, start_time = 25)
		#st.title("SkiLL_HuB : Learning Recommendation System")
			
	#st.write("Learning Recommendation System")
	#st.write("Exploring Courses on Coursera")
		st.sidebar.write(" ")
		
		
		st.sidebar.write(" ")
		st.sidebar.write(" ")
		st.sidebar.write(" ")
		st.sidebar.title("Welcome to SkiLL_HuB")
		
		st.sidebar.header("The willingness to keep learning is the most important thing about trying to be good at anything.")

		st.subheader("About the Project")
		st.write(" ")
		st.write("Skill Hub is a minimalistic system built to help learners"
		" navigate through the courses on Coursera, aided by a"
		" data-driven strategy. A learner could visualize different"
		" features provided in the dataset or interact with this app"
		" to find suitable courses to take. Skill Hub also can help"
		" identify suitable courses for a learner based on their"
		" learning preferences.")


	elif choice == "Recommend":
		st.sidebar.header("Filter on Preferences")
		st.write("This section is entrusted with the responsibility of"
		" analysing a filtered subset of courses based on the **skills**"
		" a learner is looking to develop. This filter can be adjusted on"
		" the sidebar.")

		#st.write("This section also finds courses similar to a selected course"
		#" based on Content-based recommendation. The learner can choose"
		#" any course that has been filtered on the basis of their skills"
		#" in the previous section.")
		#st.subheader("Recommend Courses")
		prep_for_cbr(df)
		

	else:
		#st.subheader("A")
			st.sidebar.write(" ")
		st.sidebar.write(" ")
		st.sidebar.image(img)
		st.write(" ")		
		st.write(" ")
		st.write(" ")
		st.write("The Course Recommendation System Skill Hub we developed recommends" 
			" resources according to the needs of students, course streams that can be" 
			" considered by students to excel in their field of interest, skill,"
			" recommendations on the basis of skills, ratings, students enrolled in the course.")
		st.write(" ")
		st.subheader("Project By:")
		st.write("Archana Jadhawani")	
		st.write("Riya Nandurkar")
		st.write("Komal Gulhane")
		st.write("Renuka Mathurkar")
    	
	
	
	
if __name__=="__main__":
	main()
