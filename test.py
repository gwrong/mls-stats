import requests
import bs4

collegeWords = ['university', 'collegiate', 'college', 'NCAA', 'NAIA']       

'''
Determines if the given wikipedia page
is for a college
'''
def determineCollege(wikiURL):

    global collegeWords

    wikipediaPage = requests.get(wikiURL).text.encode('utf-8')
    soup = bs4.BeautifulSoup(wikipediaPage, "html.parser")
    resultSet = soup.body.findChildren('p')
    introText = ''
    for result in resultSet:
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
Gathers player names and college activity
if any
'''
def gatherStats():

    pageNum = 0

    mls_base_url = 'http://www.mlssoccer.com/stats/season'
    url = ''
    wiki_base_url = 'https://en.wikipedia.org/wiki/'
    wikipedia_base_url = 'https://en.wikipedia.org'
    playerList = []

    outputFile = open('output.txt', 'wb')

    while (pageNum < 11):
        if (pageNum != 0):
            url = mls_base_url + '?page=' + str(pageNum)
        else:
            url = mls_base_url
        mlsPage = requests.get(url).text.encode('utf-8')
        soup = bs4.BeautifulSoup(mlsPage, "html.parser")

        result = soup.body.find_all('td', {"data-title" : "Player"})

        #<td data-title="Player">
        for playerTag in result:
            '''
            if ('Carroll' not in playerTag.getText()):
                continue
            '''
            playerName = playerTag.getText().encode('utf-8')
            print(playerTag.getText())
            outputFile.write(bytes('~~~~~~ ', 'UTF-8'))
            outputFile.write(playerName)
            outputFile.write(bytes(' ~~~~~~\n', 'UTF-8'))
            playerList.append(playerName)
            wikipediaURL = wiki_base_url + playerName.decode('utf-8')
            wikipediaPage = requests.get(wikipediaURL).text.encode('utf-8')
            soup = bs4.BeautifulSoup(wikipediaPage, "html.parser")
            resultSet = soup(text="Youth career")

            for result in resultSet:
                parentRow = result.parent.parent
                currentRow = parentRow.find_next_sibling()
                while ("Senior career" not in str(currentRow)):
                    children = currentRow.findChildren()
                    currentRow = currentRow.find_next_sibling()
                    tagCount = 0
                    for child in children:
                        if (len(children) == 2):
                            if (tagCount == 0):
                                outputFile.write(bytes('Years: ' + child.text + '\n', 'UTF-8'))
                            if (tagCount == 1):
                                outputFile.write(bytes('Team: ' + child.text + '\n', 'UTF-8'))
                        else:
                            
                            if (tagCount == 0):
                                outputFile.write(bytes('Years: ' + child.text + '\n', 'UTF-8'))
                            if (tagCount == 2):
                                hasHyperlink = True
                                aHrefTag = child.find('a')
                                isCollege = False
                                if (aHrefTag == None):
                                    hasHyperlink = False
                                else:
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

                                outputFile.write(bytes('Team: ' + child.text + ' (' + collegeIndicator + ')\n', 'UTF-8'))
                        tagCount= tagCount + 1
                #We just want the first spot we see Youth career
                break
            outputFile.flush()
        pageNum = pageNum + 1

    outputFile.close()

gatherStats();