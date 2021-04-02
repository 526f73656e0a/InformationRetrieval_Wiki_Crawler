import requests
import re
import sys
import random
import linecache
import os
import io
import numpy as np
#the program extracts text and image data for a given topic
#and writes them in the CURRENT DIRECTORY, relative to the location the py script is invoked from
#make sure you set it properly, in case you dont want the default one

#######change these two if you add or remove topics from Wikipedia_topics
#from which line in the doc do the titles start
startingtopic = 0
#on which line the titles end
endingtopic = 681771
#how many documents in Articles
startdocs = 2000
iterator = 0
random.seed(159234)
num_value=np.random.randint(startingtopic, endingtopic+1,size=endingtopic)

def func(ndocs):
    #create folder Articles in current working directory
    path = os.getcwd()
    path = path.replace("\\","/")
    path = path+"/Articles/"
    if not os.path.isdir(path):
        os.mkdir(path)
    #print(path)
    i=0
    for i in range(ndocs):
        #this is the title we will search
        #if we have a title that is already crawled through the while loop continues until it finds a new one
        while True:
            global iterator
            value = num_value[iterator]
            iterator = iterator+1
            #print(value)
            topic =linecache.getline((os.getcwd()).replace("\\","/")+'/Wikipedia_topics'+'/Wikipedia_topics', value).strip()
            topic1 = re.sub('[\\/:?"<>|]','',topic)
            #print(topic1)
            path_t = path+topic1
            #this check wheter the topic doesnt exist in Articles
            if not os.path.isdir(path_t):
                #print(topic)
                os.mkdir(path_t)
                break

            # if the topic already exists find a new one
            else:
                continue

        #print(topic)
        #this is the config for to get the first introduction of a title
        try:
            text_config = {
                'action': 'query',
                'format': 'json',
                'titles': topic,
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
            }
            text_response = requests.get('https://en.wikipedia.org/w/api.php',params=text_config).json()
            text_page = next(iter(text_response['query']['pages'].values()))
            # Title of the wiki article
            file_name = text_page['title']
            # Since we cannot create files with certain special symbols we need to remove them before creation
            file_name = re.sub('[\\/:?"<>|]','',topic)
            # Save the txt file in the corresponding topic folder
            file1 = open(path_t+'/'+file_name+".txt","w",encoding = 'utf-8')
            file1.write(text_page['extract'])
            file1.close()
            #print(text_page['extract'])

        except:
            print("Something went wrong while fetching the text")


        #this is the config to get the images that are in the topic
        #we use this to count the number of images
        try:
            num_image_config = {
                'action': 'parse',
                'pageid': text_page['pageid'],
                'format': 'json',
                'prop': 'images'
            }
            num_image_response = requests.get('https://en.wikipedia.org/w/api.php',params=num_image_config).json()



            #now that we havae the number of images in the page, we ask for the images that are in the page with the title
            image_config = {
                'action': 'query',
                'format': 'json',
                'titles': topic,
                'prop': 'images',
                'imlimit': len(num_image_response['parse']['images'])
            }
            image_response = requests.get('https://en.wikipedia.org/w/api.php',params=image_config).json()
            image_page = next(iter(image_response['query']['pages'].values()))


            #and we  write the image files one by one in the currect directory
            #we also dont write the svg files, since as they are mostly the logos
            #modily the filename_pattern regex for to accept the proper files
            #print("writing files")
            filename_pattern = re.compile(".*\.(?:jpe?g|gif|png|JPE?G|GIF|PNG)")
            if 'images' in image_page:
                for i in range(len(image_page['images'])):

                    url_config = {
                        'action': 'query',
                        'format': 'json',
                        'titles': image_page['images'][i]['title'],
                        'prop': 'imageinfo',
                        'iiprop': 'url'
                    }
                    url_response = requests.get('https://en.wikipedia.org/w/api.php',params=url_config).json()
                    url_page = next(iter(url_response['query']['pages'].values()))
                    #print(url_page['imageinfo'][0]['url'])
                    if(filename_pattern.search(url_page['imageinfo'][0]['url'])):

                        #print("writing image "+url_page['imageinfo'][0]['url'].rsplit("/",1)[1])
                        with open(url_page['imageinfo'][0]['url'].rsplit("/",1)[1], 'wb') as handle:
                            response = requests.get(url_page['imageinfo'][0]['url'], stream=True)

                            if not response.ok:
                                print (response)


                            for block in response.iter_content(1024):
                                if not block:
                                    break

                                handle.write(block)
                        # copy the image from current directory to article directory
                        try:
                            os.rename(url_page['imageinfo'][0]['url'].rsplit("/",1)[1], path_t+'/'+url_page['imageinfo'][0]['url'].rsplit("/",1)[1])
                        except:
                            # if the image already exists we just delete it from the OG directory
                            #print("Image already exists in folder")
                            os.remove(url_page['imageinfo'][0]['url'].rsplit("/",1)[1])
        except:
            print("Something went wrong while fetching Images")

# remove folders with empty txt files
def corr_check():
    i = 0
    path = os.getcwd()
    path = path.replace("\\","/")
    path = path+"/Articles/"
    for subdir,dirs,files in os.walk(path):
        path1 = subdir+'/'
        for file in files:
            #print(path1)
            if(os.stat(path1+file).st_size==0):
                i = i+1
                try:
                    os.remove(path1+file)
                    os.rmdir(path1)
                except:
                    print('Cannot find file specified')

    return i
# return number of subfolders already present in Articles
def n_subfolders():
    i = 0
    path = os.getcwd()
    path = path.replace("\\","/")
    path = path+"/Articles/"
    for subdir in os.walk(path):
        i=i+1
    return i-1
j = 0
while True:
    ns = n_subfolders()
    docs = startdocs-ns
    if (docs<0):
        docs = 0
    func(docs)
    cc = corr_check()
    if(cc==0):
        print(str(ns)+" Articles fetched in "+str(os.getcwd())+"\\Articles")
        break
    try:
        func(cc)
    except:
        print ("Something went wrong while generating new docs")
    j+=1
#************************************references*******************************************************************
#https://www.mediawiki.org/wiki/API:Parsing_wikitext
#https://www.mediawiki.org/wiki/Extension:TextExtracts#Caveats
#https://stackoverflow.com/questions/58337581/find-image-by-filename-in-wikimedia-commons
#https://en.wikipedia.org/w/api.php?action=query&titles=File:Albert_Einstein_Head.jpg&prop=imageinfo&iiprop=url

#https://stackoverflow.com/questions/24474288/how-to-obtain-a-list-of-titles-of-all-wikipedia-articles
#for all titles
#https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz
#https://en.wikipedia.org/w/api.php?action=parse&pageid=252735&prop=images
