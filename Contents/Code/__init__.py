#opensubtitles.org
#Subtitles service allowed by www.OpenSubtitles.org

OS_API = 'http://plexapp.api.opensubtitles.org/xml-rpc'
OS_LANGUAGE_CODES = 'http://www.opensubtitles.org/addons/export_languages.php'
OS_PLEX_USERAGENT = 'plexapp.com v9.0'
#OS_PLEX_USERAGENT = 'OS Test User Agent'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']
 
OS_ORDER_PENALTY = -1   # Penalty applied to subs score due to position in sub list return by OS.org
OS_TVSHOWS_GOOD_SEASON_BONUS = 30 # Bonus applied to subs if the season match

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.Headers['User-Agent'] = 'plexapp.com v9.0'

@expose
def GetImdbIdFromHash(openSubtitlesHash, lang):
  proxy = XMLRPC.Proxy(OS_API)
  try:
    os_movieInfo = proxy.CheckMovieHash('',[openSubtitlesHash])
  except:
    return None
    
  if os_movieInfo['data'][openSubtitlesHash] != []:
    return MetadataSearchResult(
      id    = "tt" + str(os_movieInfo['data'][openSubtitlesHash]['MovieImdbID']),
      name  = str(os_movieInfo['data'][openSubtitlesHash]['MovieName']),
      year  = int(os_movieInfo['data'][openSubtitlesHash]['MovieYear']),
      lang  = lang,
      score = 90)
  else:
    return None

def opensubtitlesProxy():
  proxy = XMLRPC.Proxy(OS_API)
  username = Prefs["username"]
  password = Prefs["password"]
  if username == None or password == None:
    username = ''
    password = ''
  token = proxy.LogIn(username, password, 'en', OS_PLEX_USERAGENT)['token']
  return (proxy, token)

def getLangList():
  langList = [Prefs["langPref1"]]
  if Prefs["langPref2"] != 'None' and Prefs["langPref1"] != Prefs["langPref2"]:
    langList.append(Prefs["langPref2"])
  return langList

def logFilteredSubtitleResponseItem(item):
  #Keys available: ['ISO639', 'SubComments', 'UserID', 'SubFileName', 'SubAddDate', 'SubBad', 'SubLanguageID', 'SeriesEpisode', 'MovieImdbRating', 'SubHash', 'MovieReleaseName', 'SubtitlesLink', 'IDMovie', 'SeriesIMDBParent', 'SubDownloadsCnt', 'QueryParameters', 'MovieByteSize', 'MovieKind', 'SeriesSeason', 'IDSubMovieFile', 'SubSize', 'IDSubtitle', 'IDSubtitleFile', 'MovieFPS', 'SubSumCD', 'QueryNumber', 'SubAuthorComment', 'MovieNameEng', 'MatchedBy', 'SubHD', 'SubRating', 'SubDownloadLink', 'SubHearingImpaired', 'ZipDownloadLink', 'SubFeatured', 'MovieTimeMS', 'SubActualCD', 'UserNickName', 'SubFormat', 'MovieHash', 'LanguageName', 'UserRank', 'MovieName', 'IDMovieImdb', 'MovieYear']
  Log(' - PlexScore: %d | MovieName: %s | MovieYear: %s | MovieNameEng: %s | SubAddDate: %s | SubBad: %s | SubRating: %s | SubDownloadsCnt: %s | IDMovie: %s | IDMovieImdb: %s' % (item['PlexScore'], item['MovieName'], item['MovieYear'], item['MovieNameEng'], item['SubAddDate'], item['SubBad'], item['SubRating'], item['SubDownloadsCnt'], item['IDMovie'], item['IDMovieImdb']))

def logFilteredSubtitleResponse(subtitleResponse):
  #Prety way to display subtitleResponse in Logs sorted by PlexScore
  #Keys available: ['ISO639', 'SubComments', 'UserID', 'SubFileName', 'SubAddDate', 'SubBad', 'SubLanguageID', 'SeriesEpisode', 'MovieImdbRating', 'SubHash', 'MovieReleaseName', 'SubtitlesLink', 'IDMovie', 'SeriesIMDBParent', 'SubDownloadsCnt', 'QueryParameters', 'MovieByteSize', 'MovieKind', 'SeriesSeason', 'IDSubMovieFile', 'SubSize', 'IDSubtitle', 'IDSubtitleFile', 'MovieFPS', 'SubSumCD', 'QueryNumber', 'SubAuthorComment', 'MovieNameEng', 'MatchedBy', 'SubHD', 'SubRating', 'SubDownloadLink', 'SubHearingImpaired', 'ZipDownloadLink', 'SubFeatured', 'MovieTimeMS', 'SubActualCD', 'UserNickName', 'SubFormat', 'MovieHash', 'LanguageName', 'UserRank', 'MovieName', 'IDMovieImdb', 'MovieYear']
  Log('Current subtitleResponse has %d elements:' % len(subtitleResponse))
  for item in sorted(subtitleResponse, key=lambda k: k['PlexScore'], reverse=True):
    logFilteredSubtitleResponseItem(item)
    
def fetchSubtitles(proxy, token, part, language):
  # Download OS result based on hash and size
  Log('Looking for match for GUID %s and size %d and language %s' % (part.openSubtitleHash, part.size, language))
  #subtitleResponse = proxy.SearchSubtitles(token,[{'sublanguageid':language, 'moviehash':part.openSubtitleHash, 'moviebytesize':str(part.size)}])['data']
  proxyResponse = proxy.SearchSubtitles(token,[{'sublanguageid':language, 'moviehash':part.openSubtitleHash, 'moviebytesize':str(part.size)}])
  
  #Check Server Response status
  if proxyResponse['status'] != "200 OK":
    Log('Error return by XMLRPC proxy: %s' % proxyResponse['status'])
    filteredSubtitleResponse = False
  else:
    subtitleResponse = proxyResponse['data']
    #Log('Keys available: %s' % subtitleResponse[0].keys())
    
    #Start to score each subs
    firstScore = 50
    filteredSubtitleResponse = []
    for sub in subtitleResponse:
      #add default score
      sub['PlexScore'] = firstScore;
      filteredSubtitleResponse.append(sub)
      firstScore = firstScore + OS_ORDER_PENALTY

    Log('hash/size search result: ')
    #logFilteredSubtitleResponse(subtitleResponse)

    #Add filters for common to Movies and TVShows
  
  return filteredSubtitleResponse
    
 
def filterSubtitleResponseForMovie(subtitleResponse, proxy, token, metadata):
  imdbID = metadata.id
  if subtitleResponse == False and imdbID != '': #let's try the imdbID, if we have one...
    Log('Found nothing via hash, trying search with imdbid: ' + imdbID)
    subtitleResponse = proxy.SearchSubtitles(token,[{'sublanguageid':l, 'imdbid':imdbID}])['data']
    #Log(subtitleResponse)

    #I don't know if I can filter on the name of the movie due to some metadata agent return Movie name in an other language.

    return subtitleResponse
  
def filsterSubtitleResponseForTVShow(subtitleResponse, season):
  #I don't know if I can filter on the tvshow name as some metadata agent return TVShow name in other language.
  # I don't know if I can filter on the episode dut to some difference beteween air order and DVD order.

  filteredSubtitleResponse = []
  for sub in subtitleResponse:
    #If season match add a bonus to the score
    if int(sub['SeriesSeason']) == int(season):
      sub['PlexScore'] = sub['PlexScore'] + OS_TVSHOWS_GOOD_SEASON_BONUS

    filteredSubtitleResponse.append(sub)

  logFilteredSubtitleResponse(filteredSubtitleResponse)
  return filteredSubtitleResponse

def downloadBestSubtitle(subtitleResponse, part, language):
  #Suppress all subtitle format no supported
  if subtitleResponse != False:
      for st in subtitleResponse: #remove any subtitle formats we don't recognize
        if st['SubFormat'] not in subtitleExt:
          Log('Removing a subtitle of type: ' + st['SubFormat'])
          subtitleResponse.remove(st)
  if subtitleResponse != False:
  #Download the sub with the higest PlexScore in the filtered list.
  #TODO Perhaps choose in case of equality with Download count.
    st = sorted(subtitleResponse, key=lambda k: ['PlexScore'], reverse=True)[0] #most downloaded subtitle file for current language
    Log('Best subtitle is:')
    logFilteredSubtitleResponseItem(st)
    subUrl = st['SubDownloadLink']
    subGz = HTTP.Request(subUrl, headers={'Accept-Encoding':'gzip'}).content
    subData = Archive.GzipDecompress(subGz)
    # Supression of previous sub should be there to avoid wiping a sub not anymore in OS
    part.subtitles[Locale.Language.Match(st['SubLanguageID'])][subUrl] = Proxy.Media(subData, ext=st['SubFormat'])
  else:
    Log('No subtitles available for language ' + language)


class OpenSubtitlesAgentMovies(Agent.Movies):
  name = 'OpenSubtitles.org'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    Log(media.primary_metadata.id)
    Log(media.primary_metadata.id.split('tt')[1].split('?')[0])
    results.Append(MetadataSearchResult(
      id    = media.primary_metadata.id.split('tt')[1].split('?')[0],
      score = 100
    ))
    
  def update(self, metadata, media, lang):
    (proxy, token) = opensubtitlesProxy()
    for i in media.items:
      for part in i.parts:
        # Remove all previous subs (taken from sender1 fork)
        for l in part.subtitles:
          part.subtitles[l].validate_keys([])

        # go fetch subtilte fo each language
        for language in getLangList():
          subtitleResponse = fetchSubtitles(proxy, token, part, language)
          subtitleResponse = filterSubtitleResponseForMovie(subtitleResponse, proxy, token, metadata)
          downloadBestSubtitle(subtitleResponse, part, language)
          

class OpenSubtitlesAgentTV(Agent.TV_Shows):
  name = 'OpenSubtitles.org'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100
    ))

  def update(self, metadata, media, lang):
    (proxy, token) = opensubtitlesProxy()
    for season in media.seasons:
      # just like in the Local Media Agent, if we have a date-based season skip for now.
      if int(season) < 1900:
        for episode in media.seasons[season].episodes:
          for i in media.seasons[season].episodes[episode].items:
            Log("Show: %s, Season: %s, Ep: %s" % (media.title, season, episode))
            for part in i.parts:
              # Remove all previous subs (taken from sender1 fork)
              for l in part.subtitles:
                part.subtitles[l].validate_keys([])

              # go fetch subtilte fo each language
              for language in getLangList():
                subtitleResponse = fetchSubtitles(proxy, token, part, language)
                subtitleResponse = filsterSubtitleResponseForTVShow(subtitleResponse, season)
                downloadBestSubtitle(subtitleResponse, part, language)
                  
