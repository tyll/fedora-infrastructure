<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
 <title>#2101: comaint.py - Fedora Infrastructure - Trac</title><link rel="start" href="/fedora-infrastructure/wiki" /><link rel="search" href="/fedora-infrastructure/search" /><link rel="help" href="/fedora-infrastructure/wiki/TracGuide" /><link rel="stylesheet" href="/fedora-infrastructure/chrome/common/css/trac.css" type="text/css" /><link rel="stylesheet" href="/fedora-infrastructure/chrome/common/css/code.css" type="text/css" /><link rel="icon" href="https://fedoraproject.org/favicon.ico" type="image/x-icon" /><link rel="shortcut icon" href="https://fedoraproject.org/favicon.ico" type="image/x-icon" /><link rel="up" href="/fedora-infrastructure/ticket/2101" title="Ticket #2101" /><link rel="alternate" href="/fedora-infrastructure/attachment/ticket/2101/comaint.py?format=raw" title="Original Format" type="text/x-python; charset=iso-8859-15" /><style type="text/css">
html {
        background-color: white;
        color: black;
        font-family: Arial, Lucida Grande, sans-serif;
        font-size: .75em;
        line-height: 1.25em;
}

/* Headings */

h1 {
        margin: 1.4em 0 0 0;
        padding: 2px 25px;
        /*margin: 0.5em 0 0.5em 0;
        padding: 0;*/
        font-size: 2.2em;
  /* font-weight: normal;*/
        color: #337AAC;
        line-height: 1.0em;
   font-weight: normal;
}

h2, h3, h4, h5, h6
{
        margin: 1.4em 0 0 0;
        padding: 2px 25px;
  /* font-weight: bold;*/
  /*    color: rgb(100,135,220);*/
  color: #2963A6;
        line-height: 1.2em;
        border-bottom: 1px solid #BFBFBF;
        /*border-left: 1px solid rgb(100,135,220);*/
}

h2 {font-size: 1.25em;}
h3 {font-size: 1.25em;}
h4 {font-size: 1.15em;}
h5, h6 {font-size: 1em;}

li p {
        margin: .25em 0;
   padding: 0px;
}

li.gap {
margin-top: 0.5em;
}

a, img, img.drawing {
        border: 0;
}

dt {
        font-weight: bold;
}

/* fix problem with small font for inline code */
tt {
        font-size: 1.25em;
}

pre {
        padding: 5px;
        border: 1px solid #c0c0c0;
        font-family: courier, monospace;
        white-space: pre;
        /* begin css 3 or browser specific rules - do not remove!
        see: http://forums.techguy.org/archive/index.php/t-249849.html */
        white-space: pre-wrap;
        word-wrap: break-word;
        white-space: -moz-pre-wrap;
        white-space: -pre-wrap;
        white-space: -o-pre-wrap;
        /* end css 3 or browser specific rules */
}

table {
        margin: 0.5em 0;
        border-collapse: collapse;

}

td
{
        padding: 0.25em;
/*      border: 1px solid #c0c0c0;*/
}

td p {
        margin: 0;
        padding: 0;
}

/* standard rule ---- */
hr {
        height: 2px;
        background-color: #c0c0c0;
        border: none;
}

/* custom rules ----- to ---------- */
.hr1 {height: 3px;}
.hr2 {height: 4px;}
.hr3 {height: 5px;}
.hr4 {height: 6px;}
.hr5 {height: 7px;}
.hr6 {height: 8px;}

/* Replacement for html 3 u tag */
.u {text-decoration: underline;}

.footnotes ul {
        padding: 0 2em;
        margin: 0 0 1em;
        list-style: none;
}

.footnotes li {
}


/* eye catchers */
.warning
{
        color: red;
}

.error
{
        color: red;
}

strong.highlight
{
        background-color: #ffcc99;
        padding: 1pt;
}


/* Recent changes */

div.recentchanges table {
        border: 1px solid #e5e5e5;
}

.recentchanges p {
        margin: 0.25em;
}

.recentchanges td {
        border: none;
        border-top: 1px solid #e5e5e5;
        border-bottom: 1px solid #e5e5e5;
        vertical-align: top;
}

.rcdaybreak {
        background-color: #E5E5E5;
}

.rcdaybreak td a {
        font-size: 0.88em;
}

.rcicon1, .rcicon2 {
        text-align: center;
}

.rcpagelink {
        width: 33%;
}

.rctime {
        font-size: 0.88em;
        white-space: nowrap;
}

.rceditor {
        white-space: nowrap;
        font-size: 0.88em;
}

.rccomment {
        width: 66%;
        color: gray;
        font-size: 0.88em;
}

.rcrss {
        float: right;
}

.recentchanges[dir="rtl"] .rcrss {
        float: left;
}

/* User Preferences */

.userpref table, .userpref td {
        border: none;
}

/* CSS for new code_area markup used by Colorizer and ParserBase */

div.codearea { /* the div makes the border */
        margin: 0.5em 0;
        padding: 0;
        border: 1pt solid #AEBDCC;
        background-color: #F3F5F7;
        color: black;
}

div.codearea pre { /* the pre has no border and is inside the div */
        margin: 0;
        padding: 10pt;
        border: none;
}

a.codenumbers { /* format of the line numbering link */
        margin: 0 10pt;
        font-size: 0.85em;
        color: gray;
}

/* format of certain syntax spans */
div.codearea pre span.LineNumber {color: gray;}
div.codearea pre span.ID         {color: #000000;}
div.codearea pre span.Operator   {color: #0000C0;}
div.codearea pre span.Char       {color: #004080;}
div.codearea pre span.Comment    {color: #008000;}
div.codearea pre span.Number     {color: #0080C0;}
div.codearea pre span.String     {color: #004080;}
div.codearea pre span.SPChar     {color: #0000C0;}
div.codearea pre span.ResWord    {color: #A00000;}
div.codearea pre span.ConsWord   {color: #008080; font-weight: bold;}
div.codearea pre span.Error      {color: #FF8080; border: solid 1.5pt #FF0000;}
div.codearea pre span.ResWord2   {color: #0080ff; font-weight: bold;}
div.codearea pre span.Special    {color: #0000ff;}
div.codearea pre span.Preprc     {color: #803999;}

/********************
Note: The following have been moved to screen-common.css.
Delete these after a few days from the commit (to make sure
people won't see strange things).
*/




/*
Custom fedoraproject.org/wiki CSS stylesheet

Global-wiki styles, used by all themes.


Copyright (c) Dimitris Glezos <dimitris@glezos.com>, 2006, 2007.
License: GPL
*/


/**************************
  Helpful classes
*/

/* Stuff floating right or left */

#page .floatright {
    float: right;
    margin-right: 1em;
    border: none;
    padding: none;
}

#page .floatleft {
    float: left;
    margin-right: 1em;
    border: none;
    padding: 0;
}

#page table.floatright tr td p,
#page table.floatleft tr td p {
    padding: 0;
    margin: 0;
}

#page table.floatright td {
        border: none;
        padding:0;
}


/* Smaller text for tables */

#page table.small tr td {
    font-size: 0.85em;
}



/**************************
  Custom tables
*/

/* Table style 1
   Contrasting header row, light separating rows.
*/

#page table.t1 tr.th {
        background-color:#2963A6;
        color: #fff;
}

#page table.t1 tr.th {
        background-color:#2963A6;
        color: #fff;
        font-weight: bold;
}

#page table.t1 tr.th2 {
    background-color:#eee;
}


/* Common table cells */

#page table td.yes {
    background-color: #6eb53c;
    color: #fff;
}

#page table td.no {
    background-color: #b5523c;
    color: #fff;
}

#page table td.ok {
    background-color: #b5833c;
    color: #fff;
}

/* Various degrees of green */

#page table td.g0 {
    background-color: white;
    color: black;
}

#page table td.g1 {
    background-color: #eff8e9;
    color: black;
}

#page table td.g2 {
    background-color: #d9eecb;
    color: black;
}*/

#page table td.g3 {
    background-color: #c3e4ad;
    color: black;
}

#page table td.g4 {
    background-color: #98d070;
    color: black;
}

#page table td.g5 {
    background-color: #6eb53c;
    color: white;
}



/**************************
  Infoboxes
*/

/* common for all message boxes */

table.message {
    background: #f9f6b7 url('http://fedoraproject.org/wiki/WikiGraphics?action=AttachFile&do=get&target=NoteBackground.png') bottom repeat-x;
    border: 1px solid #c4c295;
        color: black;
}

table.note tr td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=ideaS.png') 15px 50% no-repeat;
        padding: 0.5em 0.5em 0.5em 35px;
}

table.notice tr td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=importantS.png') 15px 50% no-repeat;
        padding: 0.5em 0.5em 0.5em 35px;
}

table.warning tr td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=warningS.png') 15px 50% no-repeat;
        padding: 0.5em 0.5em 0.5em 35px;
}

table.warning2 tr td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=warningM.png') 20px 50% no-repeat #ffcbc8;
        padding: 0.5em 0.5em 0.5em 60px;
        color: black;
        height: 70px;
}

table.warning3 tr td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=stopM.png') 20px 50% no-repeat #c10e00;
        padding: 0.5em 0.5em 0.5em 60px;
        color: white;
        height: 70px;
}


/*
Custom fedoraproject.org/wiki CSS stylesheet

Global-wiki styles, used by all themes.

Copyright (c) Dimitris Glezos <dimitris@glezos.com>, 2006, 2007.
License: GPL
*/


/**************************
  Helpful classes
*/

/* Stuff floating right or left */

#page .floatright {
    float: right;
    margin-right: 1em;
    border: none;
    padding: none;
}

#page .floatleft {
    float: left;
    margin-right: 1em;
    border: none;
    padding: 0;
}

#page table.floatright tr td p,
#page table.floatleft tr td p {
    padding: 0;
    margin: 0;
}

#page table.floatright td {
        border: none;
        padding:0;
}


/* Smaller text for tables */

#page table.small tr td {
    font-size: 0.85em;
}



/**************************
  Custom tables
*/

/* Table style 1
   Contrasting header row, light separating rows.
*/

#page table.t1 tr.th {
        background-color:#2963A6;
        color: #fff;
        font-weight: bold;
}

#page table.t1 tr.th2 {
    background-color:#eee;
        border-bottom: 1px solid #c0c0c0;
}

#page table.t1 td {
        border-left: none;
    border-right: none;
/*    border-left: 1px solid #f0f0f0;
    border-right: 1px solid #f0f0f0;  */
}

/* Table style 'alt'
   No horiz borders, use of row class "even" for alternate row colors
*/

#page table.alt tr.even {
        background-color: #f6f6f6;
}

#page table.alt tr.even td {
        border-top: 1px solid #eee;
        border-bottom: 1px solid #eee;
}

/* Common table cells */

#page table td.yes {
    background-color: #6eb53c;
    color: #fff;
}

#page table td.no {
    background-color: #b5523c;
    color: #fff;
}

#page table td.ok {
    background-color: #b5833c;
    color: #fff;
}

/* Various degrees of green */

#page table td.g0 {
    background-color: white;
    color: black;
}

#page table td.g1 {
    background-color: #eff8e9;
    color: black;
}

#page table td.g2 {
    background-color: #d9eecb;
    color: black;
}*/

#page table td.g3 {
    background-color: #c3e4ad;
    color: black;
}

#page table td.g4 {
    background-color: #98d070;
    color: black;
}

#page table td.g5 {
    background-color: #6eb53c;
    color: white;
}


/**************************
  Language box (shows page translations)
*/

table.langs {
  float: right;
  background: #eee url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=flagsS.png') 95% 95% no-repeat;
  border-top: 2px #c0d0e7 solid;
  border-bottom: 2px #c0d0e7 solid;
}

table.langs tr td {
  font-weight: normal;
  border: none !important;
  margin: 0;
  padding: 0;
}

table.langs tr td p {
  margin: 0;
  padding: 0;
}


/**************************
  Message boxes
*/

/* Common for all message boxes. Gives the ability to
   create a simple message without an icon-class. */

table.message {
    background: #f9f6b7 url('http://fedoraproject.org/wiki/WikiGraphics?action=AttachFile&do=get&target=NoteBackground.png') bottom repeat-x;
    border: 1px solid #c4c295;
        color: black;
}

/* For tables with title & multiple rows (docbook-style) */
table.message tr td {
        border: none !important;
    padding: 0;
}

table.message tr:first-child td {
        padding-top: 0.5em;
        padding-bottom: 0.5em; /* If only CSS2 had a :last-child property.. */
}

/* Small-iconed messages */

/* Spaces */
table.note tr td,
table.notice tr td,
table.warning tr td {
        padding-left: 35px;
        height: 35px;
}

/* Presentation */
table.note tr:first-child td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=ideaS.png') 15px 50% no-repeat;
}

table.notice tr:first-child td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=importantS.png') 15px 50% no-repeat;
}

table.warning tr:first-child td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=warningS.png') 15px 50% no-repeat;
}

/* Large-iconed messages */

/* Spaces */
table.warning2 tr td,
table.warning3 tr td {
        height: 60px;
        padding-left: 60px;
}

/* Presentation */
table.warning2 {
        background-color: #ffcbc8;
        background-image: none;
}

table.warning2 tr:first-child td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=warningM.png') 20px 50% no-repeat;
}

table.warning3 {
        background-color: #c10e00;
        background-image: none;
        color: white;
}

table.warning3 tr:first-child td {
    background: url('http://fedoraproject.org/wiki/WikiElements?action=AttachFile&do=get&target=stopM.png') 20px 50% no-repeat;
}

</style>
 <script type="text/javascript" src="/fedora-infrastructure/chrome/common/js/trac.js"></script>
</head>
<body>


<div id="banner">

<div id="header"><a id="logo" href="https://fedorahosted.org/fedora-infrastructure/"><img src="https://fedoraproject.org/w/uploads/5/52/Infrastructure_InfrastructureTeamN1.png" alt="" /></a><hr /></div>

<form id="search" action="/fedora-infrastructure/search" method="get">
 <div>
  <label for="proj-search">Search:</label>
  <input type="text" id="proj-search" name="q" size="10" accesskey="f" value="" />
  <input type="submit" value="Search" />
  <input type="hidden" name="wiki" value="on" />
  <input type="hidden" name="changeset" value="on" />
  <input type="hidden" name="ticket" value="on" />
 </div>
</form>



<div id="metanav" class="nav"><ul><li class="first"><a href="/fedora-infrastructure/login">Login</a></li><li><a href="/fedora-infrastructure/settings">Settings</a></li><li><a accesskey="6" href="/fedora-infrastructure/wiki/TracGuide">Help/Guide</a></li><li class="last"><a href="/fedora-infrastructure/about">About Trac</a></li></ul></div>
</div>

<div id="mainnav" class="nav"><ul><li class="first"><a accesskey="1" href="/fedora-infrastructure/wiki">Wiki</a></li><li><a accesskey="2" href="/fedora-infrastructure/timeline">Timeline</a></li><li><a accesskey="3" href="/fedora-infrastructure/roadmap">Roadmap</a></li><li><a href="/fedora-infrastructure/report">View Tickets</a></li><li><a accesskey="4" href="/fedora-infrastructure/search">Search</a></li><li class="last"><a href="/fedora-infrastructure/browser">Browse Source</a></li></ul></div>
<div id="main">




<div id="ctxtnav" class="nav"></div>

<div id="content" class="attachment">


 <h1><a href="/fedora-infrastructure/ticket/2101">Ticket #2101</a>: comaint.py</h1>
 <table id="info" summary="Description"><tbody><tr>
   <th scope="col">
    File comaint.py, 0.8 kB 
    (added by toshio,  2 months ago)
   </th></tr><tr>
   <td class="message"><p>
Script to add comtainer to packages
</p>
</td>
  </tr>
 </tbody></table>
 <div id="preview">
   <table class="code"><thead><tr><th class="lineno">Line</th><th class="content">&nbsp;</th></tr></thead><tbody><tr><th id="L1"><a href="#L1">1</a></th>
<td><I><span class="code-comment">#!/usr/bin/python -tt</span></i></td>
</tr><tr><th id="L2"><a href="#L2">2</a></th>
<td><I><span class="code-comment"></span></i></td>
</tr><tr><th id="L3"><a href="#L3">3</a></th>
<td><B><span class="code-lang">import</span></b>&nbsp;sys</td>
</tr><tr><th id="L4"><a href="#L4">4</a></th>
<td><B><span class="code-lang">import</span></b>&nbsp;getpass</td>
</tr><tr><th id="L5"><a href="#L5">5</a></th>
<td></td>
</tr><tr><th id="L6"><a href="#L6">6</a></th>
<td><B><span class="code-lang">from</span></b>&nbsp;fedora.client <B><span class="code-lang">import</span></b> PackageDB</td>
</tr><tr><th id="L7"><a href="#L7">7</a></th>
<td></td>
</tr><tr><th id="L8"><a href="#L8">8</a></th>
<td><B><span class="code-lang">if</span></b>&nbsp;__name__ == <B><span class="code-string">'__main__'</span></b>:</td>
</tr><tr><th id="L9"><a href="#L9">9</a></th>
<td>&nbsp; &nbsp; <B><span class="code-lang">print</span></b> <B><span class="code-string">'Username: '</span></b>,</td>
</tr><tr><th id="L10"><a href="#L10">10</a></th>
<td>&nbsp; &nbsp; username = sys.stdin.readline().strip()</td>
</tr><tr><th id="L11"><a href="#L11">11</a></th>
<td>&nbsp; &nbsp; password = getpass.getpass(<B><span class="code-string">'Password: '</span></b>)</td>
</tr><tr><th id="L12"><a href="#L12">12</a></th>
<td></td>
</tr><tr><th id="L13"><a href="#L13">13</a></th>
<td>&nbsp; &nbsp; pkgdb = PackageDB(username=username, password=password)</td>
</tr><tr><th id="L14"><a href="#L14">14</a></th>
<td>&nbsp; &nbsp; collections = dict([(c[0][<B><span class="code-string">'id'</span></b>], c[0]) <B><span class="code-lang">for</span></b> c <B><span class="code-lang">in</span></b> pkgdb.get_collection_list(eol=False)])</td>
</tr><tr><th id="L15"><a href="#L15">15</a></th>
<td>&nbsp; &nbsp; pkgs = pkgdb.user_packages(<B><span class="code-string">'mmaslano'</span></b>, acls=[<B><span class="code-string">'owner'</span></b>, <B><span class="code-string">'approveacls'</span></b>]).pkgs</td>
</tr><tr><th id="L16"><a href="#L16">16</a></th>
<td></td>
</tr><tr><th id="L17"><a href="#L17">17</a></th>
<td>&nbsp; &nbsp; <B><span class="code-lang">for</span></b> pkg <B><span class="code-lang">in</span></b> (p <B><span class="code-lang">for</span></b> p <B><span class="code-lang">in</span></b> pkgs <B><span class="code-lang">if</span></b> p[<B><span class="code-string">'name'</span></b>].startswith(<B><span class="code-string">'perl-'</span></b>)):</td>
</tr><tr><th id="L18"><a href="#L18">18</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; c_ids = (p[<B><span class="code-string">'collectionid'</span></b>] <B><span class="code-lang">for</span></b> p <B><span class="code-lang">in</span></b> pkg[<B><span class="code-string">'listings'</span></b>] <B><span class="code-lang">if</span></b> p[<B><span class="code-string">'collectionid'</span></b>] <B><span class="code-lang">in</span></b> collections)</td>
</tr><tr><th id="L19"><a href="#L19">19</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; branches = [collections[c][<B><span class="code-string">'branchname'</span></b>] <B><span class="code-lang">for</span></b> c <B><span class="code-lang">in</span></b> c_ids]</td>
</tr><tr><th id="L20"><a href="#L20">20</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; pkgdb.edit_package(pkg[<B><span class="code-string">'name'</span></b>], comaintainers=[<B><span class="code-string">'ppisar'</span></b>], branches=branches)</td>
</tr><tr><th id="L21"><a href="#L21">21</a></th>
<td></td>
</tr><tr><th id="L22"><a href="#L22">22</a></th>
<td>&nbsp; &nbsp; sys.exit(0)</td>
</tr></tbody></table>
 </div>
 


</div>
<script type="text/javascript">searchHighlight()</script>
<div id="altlinks"><h3>Download in other formats:</h3><ul><li class="first last"><a href="/fedora-infrastructure/attachment/ticket/2101/comaint.py?format=raw">Original Format</a></li></ul></div>

</div>

<div id="footer">
 <hr />
 <a id="tracpowered" href="http://trac.edgewall.org/"><img src="/fedora-infrastructure/chrome/common/trac_logo_mini.png" height="30" width="107"
   alt="Trac Powered"/></a>
 <p class="left">
  Powered by <a href="/fedora-infrastructure/about"><strong>Trac 0.10.5</strong></a><br />
  By <a href="http://www.edgewall.org/">Edgewall Software</a>.
 </p>
 <p class="right">
  Visit the Trac open source project at<br /><a href="http://trac.edgewall.org/">http://trac.edgewall.org/</a>
 </p>
</div>



 </body>
</html>

