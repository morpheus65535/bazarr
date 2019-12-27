/* 
ASP.NET WEB FORMS PAGE METHODS EXTENSION FOR JTABLE
http://www.jtable.org
---------------------------------------------------------------------------
Copyright (C) 2011 by Halil Ýbrahim Kalkan (http://www.halilibrahimkalkan.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/
(function(d){d.extend(!0,d.hik.jtable.prototype,{_performAjaxCall:function(b,c,a,e,f){this._ajax({url:b,data:c,async:a,success:e,error:f})},_ajax:function(b){var c=this,a=d.extend({},this.options.ajaxSettings,b);null==a.data||void 0==a.data?a.data={}:"string"==typeof a.data&&(a.data=c._convertQueryStringToObject(a.data));var e=a.url.indexOf("?");-1<e&&d.extend(a.data,c._convertQueryStringToObject(a.url.substring(e+1)));a.data=JSON.stringify(a.data);a.contentType="application/json; charset=utf-8";
a.success=function(a){a=c._normalizeJSONReturnData(a);b.success&&b.success(a)};a.error=function(){b.error&&b.error()};a.complete=function(){b.complete&&b.complete()};d.ajax(a)},_submitFormUsingAjax:function(b,c,a,e){var f=this;c={record:f._convertQueryStringToObject(c)};var g=b.indexOf("?");-1<g&&d.extend(c,f._convertQueryStringToObject(b.substring(g+1)));c=JSON.stringify(c);d.ajax({url:b,type:"POST",dataType:"json",contentType:"application/json; charset=utf-8",data:c,success:function(b){b=f._normalizeJSONReturnData(b);
a(b)},error:function(){e()}})},_convertQueryStringToObject:function(b){for(var c={},a,e=/\+/g,d=/([^&=]+)=?([^&]*)/g;a=d.exec(b);)c[decodeURIComponent(a[1].replace(e," "))]=decodeURIComponent(a[2].replace(e," "));return c},_normalizeJSONReturnData:function(b){return b.hasOwnProperty("d")?b.d:b}})})(jQuery);