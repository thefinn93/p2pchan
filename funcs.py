# -*- coding: utf-8 -*-
import sys
import os
import time
import datetime
import uuid
import struct
import re
import commands

from StringIO import StringIO

import ntplib

cactusModVersion = "0.3.1"
usepynotify = 0    # set this to 1 for libnotify notifications of activity. Requires pynotify.
curl = 0           # set this to 1 if you have cURL installed (http://curl.haxx.se). It is used for text based geolocation of peers. Also the one in p2pchan.py

if usepynotify:
    import pynotify
    pynotify.init("p2pchan")

def initializeDB(conn):
  c = conn.cursor()
  try:
    c.execute("create table posts (guid text, parent text, timestamp text, bumped text, name text, email text, subject text, thumb text, file text, message text)")
  except:
    pass
  try:
    c.execute("create table hiddenposts (guid text)")
  except:
    pass

def niceip(peerid):
  return peerid # this can be used to name peers you know. I have removed my friend's IPs for obvious reasons

def getRequestPath(request):
  request_split = str(request).split()
  return request_split[1]

def formatError(text):
  return str('<body style="background-color: #fbb;"><div style="text-align: center;font-size: 3em;"><span style="padding: 5px;border-bottom: 1px solid #7A1818;border-right: 1px solid #7A1818;background-color: #fdd;color: #7A1818;">' + text + '</span></div></body>')

def timestamp(t=None):
  x = ntplib.NTPClient()
  try: # try three times
    timestamp = x.request('europe.pool.ntp.org').tx_time
  except:
    try:
      timestamp = x.request('europe.pool.ntp.org').tx_time
    except:
      timestamp = x.request('europe.pool.ntp.org').tx_time
  return int(timestamp)

def formatDate(t=None):
  if not t:
    t = datetime.datetime.fromtimestamp(timestamp())
  return t.strftime("%y/%m/%d(%a)%H:%M:%S")

def formatTimestamp(t):
  return formatDate(datetime.datetime.fromtimestamp(int(t)))

def logTimestamp():
  return formatDate(datetime.datetime.now())

def logMessage(message):
    print '[' + logTimestamp() + '] ' + message
    if message != "Initializing..." and message != "Please ensure UDP port 44545 is open." and message != "Now available on the P2PChan network." and message != "Visit http://127.0.0.1:8080 to begin." and usepynotify:
        n = pynotify.Notification("P2PChan",message, os.getcwd() + '/content/icon.png')
        if not n.show():
            print "[" + logTimestamp() + "] wtf couldn't show dbus notification!"
    
def timeTaken(time_start, time_finish):
  return str(round(time_finish - time_start, 2))

def newGUID():
  return str(uuid.uuid1())

def pageNavigator(page, numpages):
  page_navigator = "<td>"
  if page == 0:
    page_navigator += "Previous"
  else:
    previous = str(int(page) - 1)
    if previous == "0":
      previous = ""
    else:
      previous = '<input type="hidden" name="ind" value="' + previous + '">'
    page_navigator += '<form method="get" action="/">' + previous + '<input value="Previous" type="submit"></form>'

  page_navigator += "</td><td>"

  for i in xrange(int(numpages)):
    if i == int(page):
      page_navigator += "[" + str(i) + "] "
    else:
      if i == 0:
        page_navigator += '[<a href="/">' + str(i) + '</a>] '
      else:
        page_navigator += '[<a href="/?ind=' + str(i) + '">' + str(i) + '</a>] '
        
  page_navigator += "</td><td>"

  nextpage = (int(page) + 1)
  if nextpage == int(numpages):
    page_navigator += "Next</td>"
  else:
    page_navigator += '<form method="get" action="/"><input type="hidden" name="ind" value="' + str(nextpage) + '"><input value="Next" type="submit"></form></td>'

  return """<table border="1">
      <tbody>
        <tr>
          """ + page_navigator + """
        </tr>
      </tbody>
    </table>"""

def renderPage(text, p2pchan, stylesheet, replyto=False, currentpage=0, numpages=0,):
  reshtml = navhtml = ''
  parenthtml = '<input type="hidden" name="parent" value="">'
  if replyto:
    reshtml = '&#91;<a href="/">Return</a>&#93;<div class="replymode">Posting mode: Reply</div>'
    parenthtml = '<input type="hidden" name="parent" value="' + replyto + '">'
  else:
    navhtml = pageNavigator(currentpage, numpages)
  return str("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
  <title>
    P2PChan
  </title>
  <link rel="stylesheet" type="text/css" href="/css/global.css">
  <link rel="stylesheet" type="text/css" href="/css/""" + stylesheet + """.css" title=\"""" + stylesheet + """\">
  <script type="text/javascript" src="/content/cactusmod.js"></script>
  <meta http-equiv="content-type" content="text/html;charset=UTF-8">
  <meta http-equiv="pragma" content="no-cache">
  <meta http-equiv="expires" content="-1">
</head>
<body>
    <div class="adminbar">
      [<a href="/manage">Manage</a>]
    </div>
    <div class="logo" onclick="top.location.href='/';">
      P2PChan
    </div>
    <hr width="90%" size="1">""" + reshtml + """
    <div class="postarea">
      <script type="text/javascript">
        function toEntity()
        {
          var aa = document.getElementById('mescont').value;
          var bb = '';
          for(i=0; i<aa.length; i++)
            if(aa.charCodeAt(i)>127)
              bb += '&#' + aa.charCodeAt(i) + ';';
            else
              bb += aa.charAt(i);
          document.getElementById('mescont').value = bb;
        }
        </script>
      <form name="postform" id="postform" action="/" method="post" enctype="multipart/form-data">
      """ + parenthtml + """
      <table><tr><td><iframe src="http://geoiptool.com/webapi.php?type=1&LANG=en" height="275" width="200" frameborder="0" scrolling="no" id="ipmap"></iframe></td>
      <td>
      <table class="postform">
        <tbody>
          <tr>
            <td class="postblock">
              Name
            </td>
            <td>
              <input type="text" name="name" size="28" maxlength="75" accesskey="n">
            </td>
          </tr>
          <tr>
            <td class="postblock">
              E-mail
            </td>
            <td>
              <input type="text" name="email" size="28" maxlength="75" accesskey="e">
            </td>
          </tr>
          <tr>
            <td class="postblock">
              Subject
            </td>
            <td>
              <input type="text" name="subject" size="40" maxlength="75" accesskey="s">
              <input type="button" onclick="toEntity(); document.getElementById('postform').submit();" value="Submit" accesskey="z">
            </td>
          </tr>
          <tr>
            <td class="postblock">
              Message
            </td>
            <td>
              <textarea name="message" id="mescont" cols="48" rows="4" accesskey="m"></textarea>
            </td>
          </tr>
          <tr>
            <td class="postblock">
              File
            </td>
            <td>
              <input type="file" name="file" size="35" accesskey="f">
            </td>
          </tr>
          <tr>
            <td class="postblock">
             Host
            </td>
            <td>
             <select name="host"><option value="imgur">imgur</option><option value="distibuted" selected="selected">Distributed</option></select>
            </td>
          </tr>
          <tr>
            <td colspan="2" class="rules">
              <ul>
                <li>Supported file types are: GIF, JPG, PNG</li>
                <li>Images greater than 90x90 pixels will be thumbnailed.</li>
                """ + listmissingthreads(p2pchan) + """
                <li id="peerlist">""" + peerlist(p2pchan) + """</li>
              </ul>
            </td>
          </tr>
        </tbody>
      </table>
     </td></tr></table>
      </form>
    </div>
    <hr>
    <form name="delform" action="/manage" method="get">
    """ + text.encode('utf8', 'replace') + """
    <table align="right"><tr><td nowrap align="right">
    <input type="submit" name="refresh" value="Refresh Checked Thread" class="managebutton"> 
    <input type="submit" name="hide" value="Hide Checked Post" class="managebutton">
    </td></tr></table>
    </form>
    """ + navhtml + """
    <div class="footer" style="clear: both;">
      - <a href="http://p2pchan.info">p2pchan</a> -
    </div>
</body>
</html>""")

def renderManagePage(text, stylesheet):
  return str("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
  <title>
    P2PChan
  </title>
  <link rel="stylesheet" type="text/css" href="/css/global.css">
  <link rel="stylesheet" type="text/css" href="/css/""" + stylesheet + """.css" title=\"""" + stylesheet + """\">
  <meta http-equiv="content-type" content="text/html;charset=UTF-8">
  <meta http-equiv="pragma" content="no-cache">
  <meta http-equiv="expires" content="-1">
</head>
<body>
    <div class="adminbar">
      [<a href="/">Return</a>]
    </div>
    <div class="logo">
      P2PChan
    </div>
    <hr width="90%" size="1">
    """ + text + """
    <br clear="left">
    <hr width="90%" size="1">
    <div class="footer" style="clear: both;">
      - <a href="http://p2pchan.info">p2pchan</a> -
    </div>
</body>
</html>""")

def formatMessage(message):
  message = re.compile(r'&gt;&gt;&gt;([0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12})').sub('<a href="/?res=' + r'\1' + '">&gt;&gt;&gt;&shy;' + r'\1' + '</a>', message)
  message = re.compile(r'&gt;&gt;([0-9A-Za-z]{5})').sub('<a href="#' + r'\1' + '">&gt;&gt;' + r'\1' + '</a>', message)
  message = re.compile(r'\*\*([^\s](|.*?[^\s])\**)\*\*').sub('<b>' + r'\1' + '</b>', message)
  message = re.compile(r'//([^\s](|.*?[^\s])/*)//').sub('<i>' + r'\1' + '</i>', message)
  message = re.compile(r'``([^\s](|.*?[^\s])`*)``').sub('<code>' + r'\1' + '</code>', message)
  message = re.compile(r'^&gt;(.*)$', re.MULTILINE).sub(r'<span class="unkfunc">&gt;\1</span>', message)
  return message.replace("\n", "<br>")

def buildPost(post, conn, numreplies=-1):
  POST_GUID = 0
  POST_PARENT = 1
  POST_TIMESTAMP = 2
  POST_BUMPED = 3
  POST_NAME = 4
  POST_EMAIL = 5
  POST_SUBJECT = 6
  POST_THUMB = 7
  POST_FILE = 8
  POST_MESSAGE = 9
  html = onclick = ""
  message = formatMessage(post[POST_MESSAGE])

  c = conn.cursor()
  c.execute('select count(*) from hiddenposts where guid = \'' + post[POST_GUID] + '\'')
  for row in c:
    if row[0] > 0:
      return ""

  if numreplies == -1:
    onclick = ' onclick="javascript:document.postform.message.value = document.postform.message.value + \'>>' + post[POST_GUID][0:5] + '\';return false;"'

  if post[POST_PARENT] == "" and post[POST_FILE] != "":
    html += '<a target="_blank" href="' + post[POST_FILE] + '"><img src="' + post[POST_THUMB] + '" width="90" height="90" alt="' + post[POST_GUID] + '" class="thumb"></a>'
  else:
    html += """<table>
    <tbody>
    <tr>
    <td class="doubledash">
      &#0168;
    </td>""" + \
    '<td class="reply" id="' + post[POST_GUID] + '">'
  html += '<a name="' + post[POST_GUID][0:5] + '"></a>' + \
  '<label><input type="checkbox" name="post" value="' + post[POST_GUID] + '"> '
  if post[POST_SUBJECT] != '':
    html += '<span class="filetitle">' + post[POST_SUBJECT] + '</span> '
  html += '<span class="postername">'
  if post[POST_EMAIL] != '':
    html += '<a href="mailto:' + post[POST_EMAIL] + '">'
  if post[POST_NAME] != '':
    html += post[POST_NAME]
  else:
    html += 'Anonymous'
  if post[POST_EMAIL] != '':
    html += '</a>'
  html += '</span> ' + \
  formatTimestamp(post[POST_TIMESTAMP]) + \
  '</label> ' + \
  '<span class="reflink">' + \
  '<a href="#' + post[POST_GUID][0:5] + '">ID:</a><a href="#' + post[POST_GUID][0:5] + '"' + onclick + '>' + post[POST_GUID][0:5] + '</a> ' + \
  '</span>'
  if post[POST_PARENT] == '':
    if numreplies > -1:
      html += ' [<a href="/?res=' + post[POST_GUID] + '">Reply</a>]'
  elif post[POST_FILE] != '':
    html += '<br>' + \
    '<a target="_blank" href="' + post[POST_FILE] + '"><img src="' + post[POST_THUMB] + '" width="90" height="90" alt="' + post[POST_GUID] + '" class="thumb"></a>'
  html += '<blockquote>' + message + '</blockquote>'
  if numreplies > 5:
    html += '<span class="omittedposts">' + str(numreplies - 5) + ' post'
    if numreplies > 6:
      html += 's'
    html += ' omitted.  Click Reply to view.</span>'
  if post[POST_PARENT] != '':
    html += '</td>' + \
    '</tr>' + \
    '</tbody>' + \
    '</table>'
  return html

def toEntity(data):
  res = ''
  i = 0
  while i < len(data):
    if ord(data[i]) > 127:
      if i+1 < len(data):
        res += '&#' + str(((ord(data[i]) & 0x1F) << 6) + (ord(data[i+1]) & 0x7F)) + ';'
        i += 1
      else:
        res += '?'
    else:
      res += data[i]
    i += 1
  return res

def encodePostData(post):
  return chr(27).join(post)

def decodePostData(postdata):
  return [x.replace("'", '&#39;').replace('"', '&quot;').replace("<", '&lt;').replace(">", '&gt;') for x in postdata.split(chr(27))]

def parseImageHostResponse(response):
  if 'rsp' not in response or 'error_code' in response:
    return []
  
  original_image = response[(response.find("<original_image>") + 16):response.find("</original_image>")]
  small_thumbnail = response[(response.find("<small_thumbnail>") + 17):response.find("</small_thumbnail>")]
  return [original_image, small_thumbnail]

def havePostWithGUID(guid, conn):
  c = conn.cursor()
  c.execute('select count(*) from posts where guid = \'' + guid.replace("'", '&#39;') + '\'')
  for row in c:
    if row[0] > 0:
      return True
  return False

def localFile(filename):
  return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), filename)

def getImageInfo(data):
    data = str(data)
    size = len(data)
    height = -1
    width = -1
    content_type = ''

    # handle GIFs
    if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
        # Check to see if content_type is correct
        content_type = 'image/gif'
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)

    # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
    # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
    # and finally the 4-byte width, height
    elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
          and (data[12:16] == 'IHDR')):
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)

    # Maybe this is for an older PNG version.
    elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        content_type = 'image/png'
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)

    # handle JPEGs
    elif (size >= 2) and data.startswith('\377\330'):
        content_type = 'image/jpeg'
        jpeg = StringIO(data)
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = jpeg.read
                while (ord(b) == 0xFF): b = jpeg.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    jpeg.read(3)
                    h, w = struct.unpack(">HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
                b = jpeg.read(1)
            width = int(w)
            height = int(h)
        except struct.error:
            pass
        except ValueError:
            pass

    return content_type, width, height

def peerlist(p2pchan):
    output = ""
    if len(p2pchan.kaishi.peers) != 1:
        output = "There are currently " + str(len(p2pchan.kaishi.peers)) + " other users online [<a href=\"javascript:void(0);\" onclick=\"refreshProvider()\">Refresh Peer Provider</a>]<span id=\"refreshprovider\"></span>\n<ul>\n"
    else:
        output = "There is currently " + str(len(p2pchan.kaishi.peers)) + " other user online [<a href=\"javascript:void(0);\" onclick=\"refreshProvider()\">Refresh Peer Provider</a>]<span id=\"refreshprovider\"></span>\n<ul>\n"
    for ip in p2pchan.kaishi.peers:
        if curl:
            output = output + "\n<li><a href=\"javascript:void(0)\" onclick=\"showIP('" + ip.partition(':')[0] + "')\">" + niceip(ip) + "</a> - " + commands.getoutput("curl -s \"http://www.geody.com/geoip.php?ip=" + ip.partition(':')[0] + "\" | sed '/^IP:/!d;s/<[^>][^>]*>//g'") + "</li>"
        else:
            output = output + "\n<li><a href=\"javascript:void(0)\" onclick=\"showIP('" + ip.partition(':')[0] + "')\">" + niceip(ip) + "</a></li>"
    output = output + "</ul>\n";
    return output

def listmissingthreads(p2pchan):
  import sqlite3
  output = ''
  missingthreads = []
  conn = sqlite3.connect(localFile('posts.db'))
  c = conn.cursor()
  c2 = conn.cursor()
  c.execute('select * from posts where parent != \'\'')
  for post in c:
    c2.execute('select count(*) from posts where guid = \'' + post[1] + '\'')
    for row in c2:
      if row[0] == 0 and post[1] not in missingthreads:
        missingthreads.append(post[1])
  if len(missingthreads) > 0:
    output += "<li>You have " + str(len(missingthreads)) + " missing threads:\n<ul>"
    for missingthread in missingthreads:
      output += '<li>' + missingthread + ' - <a href="javascript: void(0);" onclick="getthread(\'' + missingthread + '\',this)">Request thread</a></li>'
    output += "</ul></li>"
  else:
    output += "<li>You have no missing threads</li>"
  return str(output)

def cactus(p2pchan,request,stylesheet):
  if 'refreshpeers' in request.args:
    p2pchan.kaishi.fetchPeersFromProvider()
    return "Peers Refreshed"
  if 'peerlist' in request.args:
    return peerlist(p2pchan)
  if 'missingthreads' in request.args:
    return listmissingthreads(p2pchan)
  if 'getthread' in request.args:
    p2pchan.kaishi.sendData('THREAD', request.args['getthread'][0])
    return 'Request sent. Go to thread'
  else:  # I had been calling my version "cactus mod", and have been removing that before putting it on git, but 
    text = """<div class="logo"><img src="/content/icon.png"> Cactus Mod v""" + cactusModVersion + """</div>
<div id="cactusmodbox" style="background-color: #AAFFAA; font-family: arial; color: #AA0000;">Cactus Mod is my modification of P2PChan, currently at version """ + cactusModVersion + """. I have lots of things I wish to do with it, and am always coming up with new ones. Here's a short list of them. If you have anything else you want feel free to ask.
<ul>
<li>Encrypted/signed messages. Probably using PGP</li>
</ul>"""
    return renderManagePage(text,stylesheet)
