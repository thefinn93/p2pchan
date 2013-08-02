function refreshPeers()
 {
 xhr = new XMLHttpRequest;
 xhr.onreadystatechange=function()
  {
  if(xhr.readyState == 4)
   {
   if(xhr.status == 200)
    {document.getElementById('peerlist').innerHTML = xhr.responseText;}
   else
    {document.getElementById('peerlist').innerHTML = "<font color=\"#FF0000\"><b>Could not retrieve peerlist</b></font>";}
   }
  }
 xhr.open("GET","/cactus?peerlist=" + Math.random(),true)
 xhr.send(null)
 }


function refreshProvider()
 {
 document.getElementById('refreshprovider').innerHTML = "<img src=\"/content/throbber_arrow.gif\" />";
 xhr = new XMLHttpRequest;
 xhr.onreadystatechange=function()
  {
  if(xhr.readyState == 4)
   {
   if(xhr.status == 200)
    {document.getElementById('refreshprovider').innerHTML = xhr.responseText;}
   else
    {document.getElementById('refreshprovider').innerHTML = "<font color=\"#FF0000\"><b>Could not refresh peer provider. Is P2PChan still running?</b></font>";}
   }
  }
 xhr.open("GET","/cactus?refreshpeers=" + Math.random(),true)
 xhr.send(null)
 }

function getthread(thread,elm)
 {
 elm.innerHTML = "<img src=\"/content/throbber_arrow.gif\" />";
 elm.removeAttribute('onlcick');
 elm.removeAttribute('href');
 xhr = new XMLHttpRequest;
 xhr.onreadystatechange=function()
  {
  if(xhr.readyState == 4)
   {
   if(xhr.status == 200)
    {elm.innerHTML = "<a href=\"/?res=" + thread + "\">" + xhr.responseText + "</a>";}
   else
    {elm.innerHTML.innerHTML = "<font color=\"#FF0000\"><b>Failed to fetch thread. Is P2PChan still running?</b></font>";}
   }
  }
 xhr.open("GET","/cactus?getthread=" + thread + "&rand=" + Math.random(),true)
 xhr.send(null)
 }

setInterval('refreshPeers()', 500)
