import requests
import bs4
import sys
import json
import _thread

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
    year = 2015

    url = ''
    wiki_base_url = 'https://en.wikipedia.org/wiki/'
    wikipedia_base_url = 'https://en.wikipedia.org'
    
    playerList = []

    playersDict = dict()

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
                if ('Landon Donovan' not in playerTag.getText()):
                    continue
                '''

                playerName = playerTag.getText()

                #_thread.start_new_thread(speak, (playerName,))
                
                
                #Check if we have already looked up that player's info
                if (playerName not in playersDict):
                    playersDict[playerName] = dict()
                    playersDict[playerName]['youth'] = []
                    playersDict[playerName]['yearsPlayed'] = []
                    playersDict[playerName]['yearsPlayed'].append(year)
                    playersDict[playerName]['mlsPage'] = []
                    playersDict[playerName]['mlsPage'].append(str(year) + ', ' + str(pageNum))
                    playerFile.write(playerName + '\n')
                else:
                    #Player has already been looked up
                    print("Player " + playerName + " has already been looked up")
                    playerFile.write(playerName + ' - SKIPPED\n')
                    playersDict[playerName]['yearsPlayed'].append(year)
                    playersDict[playerName]['mlsPage'].append(str(year) + ', ' + str(pageNum))
                    continue

                print(playerTag.getText())
                #outputFile.write('~~~~~~ ' + playerName + ' ~~~~~~\n')
                #playerList.append(playerName)
                
                playerFile.flush()

                try:

                    #Look for the player's youth career in Wikipedia
                    #to locate college
                    wikipediaURL = wiki_base_url + playerName
                    wikipediaPage = requests.get(wikipediaURL).text
                    soup = bs4.BeautifulSoup(wikipediaPage, "html.parser")
                    resultSet = soup(text="Youth career")

                    if (len(resultSet) == 0):
                        #outputFile.write('No Youth Career section\n')
                        print('No Youth Career section')


                    clubEntries = []

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
                                        #outputFile.write('Years: ' + child.text + '\n')
                                        clubEntries.append(child.text)
                                    if (tagCount == 1):
                                        #outputFile.write('Team: ' + child.text + '\n')
                                        clubEntries.append(child.text)
                                else:
                                    #print(str(tagCount) + str(child))
                                    if (tagCount == 0):
                                        #outputFile.write('Years: ' + child.text + '\n')
                                        clubEntries.append(child.text)
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

                                        #outputFile.write('Team: ' + child.text + ' (' + collegeIndicator + ')\n')
                                        clubEntries.append(child.text + ' (' + collegeIndicator + ')')

                                tagCount= tagCount + 1

                            #Advance to the next table row
                            currentRow = currentRow.find_next_sibling()

                        #Zip up all year, club tuples from our list
                        zippedClubEntries = list(zip(clubEntries[0::2], clubEntries[1::2]))

                        playersDict[playerName]['youth'] = [x + ', ' + y for x, y in zippedClubEntries]
                        #print(playersDict[playerName])
                        
                        #We just want the first spot we see Youth career
                        break

                    #print(playersDict[playerName])

                    nationalTeamResultSet = soup(text="National team")

                    clubEntries = dict()
                    clubEntries['ntlYears'] = []
                    clubEntries['ntlTeam'] = []
                    clubEntries['ntlApps'] = []
                    clubEntries['ntlGoals'] = []

                    for result in nationalTeamResultSet:
                        parentRow = result.parent.parent
                        currentRow = parentRow.find_next_sibling()
                        

                        #Keep going through the table until we hit the next section
                        while (currentRow != None):
                            
                            children = currentRow.findChildren()
                            tagCount = 0

                            for child in children:

                                #There seem to be 2 different structures for the
                                #youth career section. Will need to investigate
                                #print(child.text + str(tagCount))
                                if (tagCount == 0):
                                    clubEntries['ntlYears'].append(child.text)

                                if (tagCount == 1):
                                    x=5
                                    
                                if (tagCount == 2):
                                    clubEntries['ntlTeam'].append(child.text)
                                    
                                if (tagCount == 3):
                                    x=5
                                    
                                if (tagCount == 4):
                                    clubEntries['ntlApps'].append(child.text)

                                if (tagCount == 5):
                                    clubEntries['ntlGoals'].append(child.text)
                                    

                                tagCount += 1

                            currentRow = currentRow.find_next_sibling()
                    
                    zippedNationalEntries = list(zip(clubEntries['ntlYears'], clubEntries['ntlTeam'], clubEntries['ntlApps'], clubEntries['ntlGoals']))
                    playersDict[playerName]['national'] = [w + ', ' + x + ', ' + y + ', ' + z  for w, x, y, z in zippedNationalEntries]

                except Exception as e:
                    print("Error occurred: " + str(e) + "\n")

                #outputFile.flush()
            #Advance to the next page of this season
            pageNum = pageNum + 1

        year -= 1

    outputFile.write(json.dumps(playersDict, indent=4, sort_keys=True) + '\n')

    outputFile.write("Number of unique players: " + str(len(playersDict.keys())))

    #Close dem file handlers
    outputFile.close()
    playerFile.close()

    
'''
Convert the saved json file from above
to an excel file
'''
def convertToExcel():

    with open('output.txt') as data_file:    
        data = json.load(data_file)

    excelFile = open('mls-excel.csv', 'wb')
    excelFile.write('Player,mlsYears,youthYears,youthTeam,ntlCaps'.encode('utf-8'))
    excelFile.write('\n'.encode('utf-8'))
    print(data)
    for player in data.keys():
        excelFile.write(player.encode('utf-8'))
        excelFile.write(','.encode('utf-8'))

        mlsYears = len(data[player]['yearsPlayed'])
        excelFile.write(str(mlsYears).encode('utf-8'))

        youthList = data[player]['youth']
        if (len(youthList) > 0):

            #Convert weird symbols to dashes
            
            years = youthList[-1].split(',')[0].replace('\u2013', '-')
            print(youthList[-1].split(',')[1])
            excelFile.write(','.encode('utf-8'))
            excelFile.write(years.encode('utf-8'))
            excelFile.write(','.encode('utf-8'))
            excelFile.write(youthList[-1].split(',')[1].encode('utf-8'))
            excelFile.write(','.encode('utf-8'))

            capSum = 0
            for entry in data[player]['national']:
                try:
                    capSum += int(entry.split(',')[2])
                except:
                    print('Invalid caps: ' + str(player))

            excelFile.write(str(capSum).encode('utf-8'))

        excelFile.write('\n'.encode('utf-8'))

    excelFile.close()

'''
Text to speech for fun
'''
def speak(toSpeak):

    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Speak(toSpeak)

#gatherStats();
convertToExcel()
#speak()