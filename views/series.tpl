<html>
	<head>
		<!DOCTYPE html>
		<script src="{{base_url}}/static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}/static/jquery/jquery.mobile.vmouse.min.js"></script>
		<script src="{{base_url}}/static/semantic/semantic.min.js"></script>
		<script src="{{base_url}}/static/jquery/tablesort.js"></script>
		<link rel="stylesheet" href="{{base_url}}/static/semantic/semantic.min.css">
		
		<link rel="apple-touch-icon" sizes="120x120" href="{{base_url}}/static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="{{base_url}}/static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="{{base_url}}/static/favicon-16x16.png">
		<link rel="manifest" href="{{base_url}}/static/manifest.json">
		<link rel="mask-icon" href="{{base_url}}/static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="{{base_url}}/static/favicon.ico">
		<meta name="msapplication-config" content="{{base_url}}/static/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">
		
		<title>Bazarr</title>
		
		<style>
			body {
				background-color: #272727;
			}
			#divmenu {
				background-color: #272727;
				opacity: 0.9;
				padding-top: 2em;
				padding-bottom: 1em;
				padding-left: 1em;
				padding-right: 128px;
			}
			#fondblanc {
				background-color: #ffffff;
				border-radius: 0px;
				box-shadow: 0px 0px 5px 5px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding: 2em 3em 2em 3em;
			}
			#tableseries {
				padding-top: 1em;
			}
			#divdetails {
				min-height: 250px;
			}
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
		   	<div class="ui indeterminate text loader">Loading...</div>
		</div>
		<div id="divmenu" class="ui container">
			<div style="background-color:#272727;" class="ui inverted borderless labeled icon huge menu five item">
				<a href="{{base_url}}/"><img style="margin-right:32px;" class="logo" src="{{base_url}}/static/logo128.png"></a>
				<div style="height:80px;" class="ui container">
					<a class="item" href="{{base_url}}/">
						<i class="play icon"></i>
						Series
					</a>
					<a class="item" href="{{base_url}}/history">
						<i class="wait icon"></i>
						History
					</a>
					<a class="item" href="{{base_url}}/wanted">
						<i class="warning sign icon"></i>
						Wanted
					</a>
					<a class="item" href="{{base_url}}/settings">
						<i class="settings icon"></i>
						Settings
					</a>
					<a class="item" href="{{base_url}}/system">
						<i class="laptop icon"></i>
						System
					</a>
				</div>
			</div>
		</div>
			
		<div id="fondblanc" class="ui container">
			<div class="ui basic buttons">
				<button id="update_series" class="ui button"><i class="refresh icon"></i>Update Series</button>
				<button id="update_all_episodes" class="ui button"><i class="refresh icon"></i>Update All Episodes</button>
				<button id="add_new_episodes" class="ui button"><i class="wait icon"></i>Add New Episodes</button>
			</div>

			<table id="tableseries" class="ui very basic selectable sortable table">
				<thead>
					<tr>
						<th class="sorted ascending">Name</th>
						<th>Path</th>
						<th>Language</th>
						<th>Hearing-impaired</th>
						<th class="no-sort"></th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import os
				%for row in rows:
					<tr class="selectable">
						<td><a href="{{base_url}}/episodes/{{row[5]}}">{{row[1]}}</a></td>
						<td>
						{{row[2]}}
						</td>
						<td>
							%subs_languages = ast.literal_eval(str(row[3]))
							%if subs_languages is not None:
								%for subs_language in subs_languages:
									<div class="ui tiny label">{{subs_language}}</div>
								%end
							%end
						</td>
						<td>{{row[4]}}</td>
						<td {{!"style='background-color: yellow;'" if row[4] == None else ""}}>
							<%
							subs_languages_list = []
							if subs_languages is not None:
								for subs_language in subs_languages:
									subs_languages_list.append(subs_language)
								end
							end
							%>
							<div class="config ui inverted basic compact icon" data-tooltip="Edit series" data-inverted="" data-tvdbid="{{row[0]}}" data-title="{{row[1]}}" data-poster="{{row[6]}}" data-languages="{{!subs_languages_list}}" data-hearing-impaired="{{row[4]}}">
								<i class="ui black configure icon"></i>
							</div>
						</td>
					</tr>
				%end
				</tbody>
			</table>
		</div>

		<div class="ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<div id="series_title"></div>
			</div>
			<div class="content">
				<form name="series_form" id="series_form" action="" method="post" class="ui form">
					<div id="divdetails" class="ui grid">
						<div class="four wide column">
							<img id="series_poster" class="ui image" src="">
						</div>
						<div class="twelve wide column">
							<div class="ui grid">
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Languages</label>
									</div>
									<div class="nine wide column">
										<select name="languages" id="series_languages" multiple="" class="ui fluid selection dropdown">
											<option value="">Languages</option>
											%for language in languages:
											<option value="{{language[0]}}">{{language[1]}}</option>
											%end
										</select>
									</div>
								</div>
								<div class="middle aligned row">
									<div class="right aligned five wide column">
										<label>Hearing-impaired</label>
									</div>
									<div class="nine wide column">
										<div id="series_hearing-impaired_div" class="ui toggle checkbox">
									    	<input name="hearing_impaired" id="series_hearing-impaired" type="checkbox">
									    	<label></label>
									    </div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</form>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Cancel</button>
				<button type="submit" name="save" value="save" form="series_form" class="ui blue approve button">Save</button>
			</div>
		</div>
	</body>
</html>


<script>
	if (sessionStorage.scrolly) {
	    $(window).scrollTop(sessionStorage.scrolly);
	    sessionStorage.clear();
	}

	$('table').tablesort();

	$('a, button:not(.cancel)').bind('click vtouch', function(){
		$('#loader').addClass('active');
	})

	$('.modal')
		.modal({
	    	autofocus: false
		})
	;

	$('#update_series').bind('click vtouch', function(){
		window.location = '{{base_url}}/update_series';
	})

	$('#update_all_episodes').bind('click vtouch', function(){
		window.location = '{{base_url}}/update_all_episodes';
	})

	$('#add_new_episodes').bind('click vtouch', function(){
		window.location = '{{base_url}}/add_new_episodes';
	})

	$('.config').bind('click vtouch', function(){
		sessionStorage.scrolly=$(window).scrollTop();

		$('#series_form').attr('action', '{{base_url}}/edit_series/' + $(this).data("tvdbid"));

		$("#series_title").html($(this).data("title"));
		$("#series_poster").attr("src", "{{base_url}}/image_proxy" + $(this).data("poster"));
		
		$('#series_languages').dropdown('clear');
		var languages_array = eval($(this).data("languages"));
		$('#series_languages').dropdown('set selected',languages_array);
		
		if ($(this).data("hearing-impaired") == "True") {
			$("#series_hearing-impaired_div").checkbox('check');
		} else {
			$("#series_hearing-impaired_div").checkbox('uncheck');
		}
		
		$('.small.modal').modal('show');
	})

	$('#series_languages').dropdown();

</script>