<!DOCTYPE html>
<html lang="en">
	<head>
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
				border-radius: 0;
				box-shadow: 0 0 5px 5px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding: 2em 3em 2em 3em;
			}
			#tableseries {
				padding-top: 1em;
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
			<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
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
						<th>Audio Language</th>
						<th>Subtitles Language(s)</th>
						<th>Hearing-Impaired</th>
						<th>Forced</th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import os
				%for row in rows:
					<tr class="selectable">
						<td class="collapsing">
							<div class="ui checkbox">
								<input id='{{row['sonarrSeriesId']}}' type="checkbox" class="selected">
								<label></label>
							</div>
						</td>
						<td><a href="{{base_url}}episodes/{{row['sonarrSeriesId']}}">{{row['title']}}</a></td>
						<td>{{row['audio_language']}}</td>
						<td>
							%subs_languages = ast.literal_eval(str(row['languages']))
							%if subs_languages is not None:
								%for subs_language in subs_languages:
									<div class="ui tiny label">{{subs_language}}</div>
								%end
							%end
						</td>
						<td>{{!"" if row['hearing_impaired'] is None else row['hearing_impaired']}}</td>
						<td>{{!"" if row['forced'] is None else row['forced']}}</td>
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
			      		<label style='color: white;'>Subtitles Language(s)</label>
			      		<select name="languages" {{!'multiple="" ' if single_language is False else ''}}class="select ui disabled selection dropdown">
			                <option value="">No Change</option>
			                <option value="None">None</option>
			                %for language in languages:
							<option value="{{language['code2']}}">{{language['name']}}</option>
							%end
			            </select>
			    	</div>
			    	<div class="field">
			    		<label style='color: white;'>Hearing-Impaired</label>
			    		<select name="hearing_impaired" class="select ui disabled selection dropdown">
			                <option value="">No Change</option>
			                <option value="True">True</option>
			                <option value="False">False</option>
			            </select>
			    	</div>
			    	<div class="field">
			    		<label style='color: white;'>Forced</label>
			    		<select name="forced" class="select ui disabled selection dropdown">
			                <option value="">No change</option>
			                <option value="False">False</option>
			                <option value="True">True</option>
			                <option value="Both">Both</option>
			            </select>
			    	</div>
			    	<div class='field'>
						<label style='color: white;'><span id='count'>0</span> Series Selected</label>
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

	$('a, button').on('click', function(){
		$('#loader').addClass('active');
	});

	$('.modal')
		.modal({
			autofocus: false
		});

	$('.selected').on('change', function() {
		$("#count").text($('.selected:checked').length);
		if ( $('.selected:checked').length > 0 ) {
			$('.select').removeClass('disabled');
			$('#save').removeClass('disabled');
		}
		else {
			$('.select').addClass('disabled');
			$('#save').addClass('disabled');
		}

		const result = [];
		$('.selected:checked').each(function(i){
			result.push($(this).attr('id'));
		});
		$("#checked").val(result);
	});

	$('#selectall').on('change', function() {
		if ( $('#selectall').is(":checked") ) {
			$('.selected').prop('checked', true).trigger('change');
		}
		else {
			$('.selected').prop('checked', false).trigger('change');
		}
	});

	$('.select').dropdown();
</script>
