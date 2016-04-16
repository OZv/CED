uc1=0;
function opc(c){
var n=c.parentNode.nextSibling;
with(n.style)
if(display!="none"){
display="none";
c.className="yiq";
}else{
display="block";
c.className="yjp";
}
}
function aes(c,f){
c.removeAttribute("onclick");
with(c.style){
	cursor="default";outline="1px dotted gray";
}
var u="http://www.collinsdictionary.com/sounds/"+f+".mp3";
var b=function(){
	with(c.style){outline="";cursor="pointer";}
	c.setAttribute("onclick","aes(this,'"+f+"')");
	};
var t=setTimeout(b,2000);
try{
with(document.createElement("audio")){
	setAttribute("src",u);
	onloadstart=function(){clearTimeout(t);};
	onended=b;
	play();
}
}
catch(e){
c.style.outline="";
}
}
function vst(a,b,c,d){
with(a.style){backgroundColor=d;color=c;borderColor=c;}
with(b.style){backgroundColor=c;color="#FFF";borderColor=c;}
}
function rvi(c){
var p=c.parentNode;
var d=p.nextSibling;
var t=d.nextSibling;
with(c){
className='dzf';
setAttribute("onclick","javascript:void(0);");
var b=nextSibling?nextSibling:previousSibling;
var j=nextSibling?1:0;
}
with(b){
className='t3h';
setAttribute("onclick","rvi(this)");
}
if(j)vst(b,c,"#4AB0EF","#F5F7FB");else vst(b,c,"#F48040","#FDF9F7");
with(t.style)
if(display!="block"){display="block";d.style.display="none";}
else{display="none";d.style.display="block";}
}
function cmy(c,a){
for(var i=0;i<a.length;i++)
if(c==a[i])return 1;
return 0;
}
function wm4(t,c){
var d=document.getElementsByTagName(t);
for(var i=0;i<d.length;i++)
with(d[i])
if(previousSibling&&cmy(className,c))
with(previousSibling){
var h=offsetHeight;
with(childNodes[1])
if(className=="yjp"&&d[i].offsetHeight>h*12){
className="yiq";
d[i].style.display="none";
}
}
}
function gxe(){
uc1=1;
wm4("div",["m6d","d3l","uoh"]);
}
if(!uc1){
if(window.addEventListener)
	window.addEventListener("load",gxe,false);
else window.attachEvent("onload",gxe);
}
