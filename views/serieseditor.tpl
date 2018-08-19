<html>
	<head>
		<!DOCTYPE html>
		<script src="{{base_url}}static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}static/semantic/semantic.min.js"></script>
		<script src="{{base_url}}static/jquery/tablesort.js"></script>
		<link rel="stylesheet" href="{{base_url}}static/semantic/semantic.min.css">

		<link rel="apple-touch-icon" sizes="120x120" href="{{base_url}}static/apple-touch-icon.png">
		<link rel="icon" type="image/png" sizes="32x32" href="{{base_url}}static/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="16x16" href="{{base_url}}static/favicon-16x16.png">
		<link rel="manifest" href="{{base_url}}static/manifest.json">
		<link rel="mask-icon" href="{{base_url}}static/safari-pinned-tab.svg" color="#5bbad5">
		<link rel="shortcut icon" href="{{base_url}}static/favicon.ico">
		<meta name="msapplication-config" content="{{base_url}}static/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">

		<title>Series Editor - Bazarr</title>

		<style>
			body {
				background-color: #272727;
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
			#bottommenu {
				background-color: #333333;
				box-shadow: 0 0 10px 1px #333;
				padding: 10px;
			}
			#bottomform {
				width: 100%;
				padding-left: 8em;
				margin-bottom: -1em !important;
			}
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
			<div class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')

		<div id="fondblanc" class="ui container">
			<table id="tableseries" class="ui very basic selectable sortable table">
				<thead>
					<tr>
						<th class="no-sort collapsing">
							<div class="ui checkbox">
								<input id='selectall' type="checkbox">
								<label></label>
							</div>
						</th>
						<th class="sorted ascending">Name</th>
						<th>Audio language</th>
						<th>Subtitles languages</th>
						<th>Hearing-impaired</th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import os
				%for row in rows:
					<tr class="selectable">
						<td class="collapsing">
							<div class="ui checkbox">
								<input id='{{row[5]}}' type="checkbox" class="selected">
								<label></label>
							</div>
						</td>
						<td><a href="{{base_url}}episodes/{{row[5]}}">{{row[1]}}</a></td>
						<td>{{row[7]}}</td>
						<td>
							%subs_languages = ast.literal_eval(str(row[3]))
							%if subs_languages is not None:
								%for subs_language in subs_languages:
									<div class="ui tiny label">{{subs_language}}</div>
								%end
							%end
						</td>
						<td>{{!"" if row[4] == None else row[4]}}</td>
					</tr>
				%end
				</tbody>
			</table>
		</div>
		<div id='bottommenu' class="ui inverted bottom fixed menu">
			<form id='bottomform' action="{{base_url}}edit_serieseditor" method="POST" class="ui form">
				<input type="hidden" name="series" id="checked" />
				<div class="fields">
			    	<div class="eight wide field">
			      		<label style='color: white;'>Subtitles languages</label>
			      		<select name="languages" {{!'multiple="" ' if single_language is False else ''}}class="select ui disabled selection dropdown">
			                <option value="">No change</option>
			                <option value="None">None</option>
			                %for language in languages:
							<option value="{{language[0]}}">{{language[1]}}</option>
							%end
			            </select>
			    	</div>
			    	<div class="field">
			    		<label style='color: white;'>Hearing-impaired</label>
			    		<select name="hearing_impaired" class="select ui disabled selection dropdown">
			                <option value="">No change</option>
			                <option value="True">True</option>
			                <option value="False">False</option>
			            </select>
			    	</div>
			    	<div class='field'>
						<label style='color: white;'><span id='count'>0</span> series selected</label>
						<button type="submit" id="save" name="save" value="save" class="ui disabled blue approve button">Save</button>
					</div>
				</div>
			</form>
		</div>

		% include('footer.tpl')
		<br><br><br><br>
	</body>
</html>


<script>
	if (sessionStorage.scrolly) {
		$(window).scrollTop(sessionStorage.scrolly);
		sessionStorage.clear();
	}

	$('table').tablesort();

	$('a, button').click(function(){
		$('#loader').addClass('active');
	})

	$('.modal')
		.modal({
			autofocus: false
		})
	;

	$('.selected').change(function() {
		$("#count").text($('.selected:checked').length);
		if ( $('.selected:checked').length > 0 ) {
			$('.select').removeClass('disabled');
			$('#save').removeClass('disabled');
		}
		else {
			$('.select').addClass('disabled');
			$('#save').addClass('disabled');
		}

		var result = [];
		$('.selected:checked').each(function(i){
			result.push($(this).attr('id'));
		});
		$("#checked").val(result);
	});

	$('#selectall').change(function() {
		if ( $('#selectall').is(":checked") ) {
			$('.selected').prop('checked', true).change();
		}
		else {
			$('.selected').prop('checked', false).change();
		}
	});

	$('.select').dropdown();
</script>