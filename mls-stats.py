import requests
import bs4
import sys

collegeWords = ['university', 'college', 'NCAA', 'NAIA']       

'''
Determines if the given wikipedia page
is for a college through keywords
'''
def determineCollege(wikiURL):

    global collegeWords

    wikipediaPage = requests.get(wikiURL).text.encode('utf-8')
    soup = bs4.BeautifulSoup(wikipediaPage, "html.parser")
    resultSet = soup.body.findChildren('p')
    introText = ''
    for result in resultSet:

        #We want to find the p tag that
        #is the page intro
        if (len(result.text) < 100):
            continue
        else:
            introText = result.text.lower()
            break

    for collegeWord in collegeWords:
        if (collegeWord.lower() in introText):
            return True
    return False

'''
Gets the GET url for the season
'''
def getURL(year, page):
    #mls_base_url = 'http://www.mlssoccer.com/stats/season'
    if (page == 0):
        return 'http://www.mlssoccer.com/stats/season?franchise=select&year=%s&season_type=REG&group=goals&op=Search&form_build_id=form-iTMqGm5AwXDmfkfwJUpHlwSeJLkyLEtFs19jEoH6veI&form_id=mp7_stats_hub_build_filter_form' % (str(year))
    else:
        return 'http://www.mlssoccer.com/stats/season?page=%s&franchise=select&year=%s&season_type=REG&group=goals&op=Search&form_build_id=form-iTMqGm5AwXDmfkfwJUpHlwSeJLkyLEtFs19jEoH6veI&form_id=mp7_stats_hub_build_filter_form' % (str(page), str(year))

'''
Gathers player names and college activity
if any
'''
def gatherStats():

    #Determines the season
    year = 2007

    url = ''
    wiki_base_url = 'https://en.wikipedia.org/wiki/'
    wikipedia_base_url = 'https://en.wikipedia.org'
    
    playerList = []

    playerDict = dict()

    outputFile = open('output.txt', 'w')
    playerFile = open('players.txt', 'w')

    #Go through all seasons
    while (year >= 1996):

        #Determines the page number within the season
        pageNum = 0

        numPlayersOnPage = sys.maxsize

        #Scroll through all mls player pages
        while (numPlayersOnPage > 0):

            print('@@@@@@@@ Working through page ' + str(pageNum) + ' of the ' + str(year) + ' season @@@@@@@@')

            #Generate the page url
            url = getURL(year, pageNum)

            mlsPage = requests.get(url).text
            soup = bs4.BeautifulSoup(mlsPage, "html.parser")

            result = soup.body.find_all('td', {"data-title" : "Player"})

            numPlayersOnPage = len(result)

            #Parse each player tag
            #<td data-title="Player">
            for playerTag in result:
                '''
                if ('Keane' not in playerTag.getText()):
                    continue
                '''
                playerName = playerTag.getText()
                print(playerTag.getText())
                outputFile.write('~~~~~~ ' + playerName + ' ~~~~~~\n')
                playerList.append(playerName)

                playerFile.write(playerTag.getText() + '\n')
                playerFile.flush()

                try:

                    #Look for the player's youth career in Wikipedia
                    #to locate college
                    wikipediaURL = wiki_base_url + playerName
                    wikipediaPage = requests.get(wikipediaURL).text
                    soup = bs4.BeautifulSoup(wikipediaPage, "html.parser")
                    resultSet = soup(text="Youth career")

                    if (len(resultSet) == 0):
                        outputFile.write('No Youth Career section\n')

                    #Loop through each youth career entry for the player
                    for result in resultSet:

                        #We located youth career, now we
                        #navigate to the next table entries
                        parentRow = result.parent.parent
                        currentRow = parentRow.find_next_sibling()

                        #Keep going through the table until we hit the next section
                        while (currentRow != None and "Senior career" not in str(currentRow)):
                            
                            children = currentRow.findChildren()
                            tagCount = 0
                            for child in children:

                                #There seem to be 2 different structures for the
                                #youth career section. Will need to investigate
                                if (len(children) == 2):
                                    if (tagCount == 0):
                                        outputFile.write('Years: ' + child.text + '\n')
                                    if (tagCount == 1):
                                        outputFile.write('Team: ' + child.text + '\n')
                                else:
                                    #print(str(tagCount) + str(child))
                                    if (tagCount == 0):
                                        outputFile.write('Years: ' + child.text + '\n')
                                    if (tagCount == 2):

                                        #Search for wiki link for team if exists
                                        hasHyperlink = True
                                        aHrefTag = None

                                        #If we already are an 'a' tag, we found it
                                        #(Sometimes we are already there, other times it is inside this tag)
                                        if (child.name == 'a'):
                                            aHrefTag = child
                                        else: #Otherwise search in this tag
                                            aHrefTag = child.find('a')
                                        
                                        isCollege = False
                                        if (aHrefTag == None):
                                            hasHyperlink = False
                                        else:
                                            #Some links are external
                                            if (not aHrefTag['href'].startswith('/wiki/')):
                                                hasHyperlink = False
                                            else:
                                                isCollege = determineCollege(wikipedia_base_url + aHrefTag['href'])
                                        collegeIndicator = ''
                                        if (not hasHyperlink):
                                            collegeIndicator = "No Wikipedia link"
                                        elif (isCollege):
                                            collegeIndicator = 'College'
                                        else:
                                            collegeIndicator = 'Not a college'

                                        outputFile.write('Team: ' + child.text + ' (' + collegeIndicator + ')\n')
                                tagCount= tagCount + 1

                            #Advance to the next table row
                            currentRow = currentRow.find_next_sibling()

                        #We just want the first spot we see Youth career
                        break

                    
                except Exception as e:
                    outputFile.write("Error occurred\n")
                
                outputFile.flush()
            #Advance to the next page of this season
            pageNum = pageNum + 1
            break

        year -= 1
        break

    #Close dem file handlers
    outputFile.close()
    playerFile.close()


gatherStats();