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

def toEntity(data):
  res = ''
  i = 0
  while i < len(data):
    if ord(data[i]) < 0x80:
      res += data[i]
      i += 1
    elif (ord(data[i]) & 0xE0 == 0xE0) and (i+2 < len(data)):
      code = ((ord(data[i]) & 0xF) << 12) | ((ord(data[i+1]) & 0x3F) << 6) | (ord(data[i+2]) & 0x3F)
      res += '&#' + str(code) + ';'
      i += 3
    elif (ord(data[i]) & 0xC0 == 0xC0) and (i+1 < len(data)):
      code = ((ord(data[i]) & 0x1F) << 6) | (ord(data[i+1]) & 0x3F)
      res += '&#' + str(code) + ';'
      i += 2
    else:
      res += '?'
      i += 1
  return res

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

def niceip(p2pchan, peerid):
  ip = peerid.split(":")[0:-1]
  nice = ":".join(ip)
  if p2pchan.config.has_section("names"):
    if p2pchan.config.has_option("names", peerid.replace(":","-")):
      nice = p2pchan.config.get("names", peerid.replace(":","-"))
  return nice

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
  <script type="text/javascript" src="/content/script.js"></script>
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
      <form name="postform" id="postform" action="/" method="post" enctype="multipart/form-data">
      """ + parenthtml + """
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
              <input type="submit" value="Submit" accesskey="z">
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
#  message = re.compile(r'//([^\s](|.*?[^\s])/*)//').sub('<i>' + r'\1' + '</i>', message)
#  message = re.compile(r'``([^\s](|.*?[^\s])`*)``').sub('<code>' + r'\1' + '</code>', message)
  message = re.compile(r'^&gt;(.*)$', re.MULTILINE).sub(r'<span class="unkfunc">&gt;\1</span>', message)

  message = re.compile(r'\*\*([^\s](|.*?[^\s])\**)\*\*').sub('<b>' + r'\1' + '</b>', message)
  message = re.compile(r'__([^\s](|.*?[^\s])\**)__').sub('<b>' + r'\1' + '</b>', message)
  message = re.compile(r'\[b\]([^\s](|.*?[^\s])\**)\[\/b\]').sub('<b>' + r'\1' + '</b>', message)

  message = re.compile(r'\[i\]([^\s](|.*?[^\s])\**)\[\/i\]').sub('<i>' + r'\1' + '</i>', message)
  message = re.compile(r'\*([^\s](|.*?[^\s])\**)\*').sub('<i>' + r'\1' + '</i>', message)

  message = re.compile(r'\[s\]([^\s](|.*?[^\s])\**)\[\/s\]').sub('<s>' + r'\1' + '</s>', message)

#TODO: [spoiler]спойлер[/spoiler], %%спойлер%% == спойлер
#TODO: [code]быдлокод();[/code] == быдлокод();

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
    html += '<a target="_blank" href="' + post[POST_FILE] + '"><img src="' + post[POST_FILE] + '" width="200" height="200" alt="' + post[POST_GUID] + '" class="thumb"></a>'
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
    '<a target="_blank" href="' + post[POST_FILE] + '"><img src="' + post[POST_THUMB] + '" width="200" height="200" alt="' + post[POST_GUID] + '" class="thumb"></a>'
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
        output = "There are currently " + str(len(p2pchan.kaishi.peers)) + " other users online\n<ul>\n"
    else:
        output = "There is currently " + str(len(p2pchan.kaishi.peers)) + " other user online\n<ul>\n"
    for ip in p2pchan.kaishi.peers:
        output = output + "\n<li>" + niceip(p2pchan, ip) + " [<a href=\"#\" onclick=\"changename('" + ip + "')\">Set/change name</a>]</li>"
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
  if 'peerlist' in request.args:
    return peerlist(p2pchan)
  elif 'missingthreads' in request.args:
    return listmissingthreads(p2pchan)
  elif 'getthread' in request.args:
    p2pchan.kaishi.sendData('THREAD', request.args['getthread'][0])
    return 'Request sent. Go to thread'
  elif 'addpeer' in request.args:
    p2pchan.kaishi.addPeer(request.args['addpeer'][0])
    return "Added " + request.args['addpeer'][0]
  elif 'setname' in request.args:
    if "name" in request.args and "ip" in request.args:
      if not p2pchan.config.has_section("names"):
        p2pchan.config.add_section("names")
      peerid = request.args['ip'][0].replace(":", "-")
      p2pchan.config.set("names", peerid, request.args['name'][0])
      f = open(localFile('p2pchan.ini'), 'w')
      p2pchan.config.write(f)
      f.close()
      return renderManagePage(peerid + " is now known as " + request.args['name'][0], stylesheet)
    else:
      return renderManagePage("Please specify a name and an IP!", stylesheet)
  else:
    text = """Lolhai"""
    return renderManagePage(text,stylesheet)
