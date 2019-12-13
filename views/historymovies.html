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
		
		<title>History - Bazarr</title>
		
		<style>
			body {
				background-color: #272727;
			}
			.fast.backward, .backward, .forward, .fast.forward {
    			cursor: pointer;
			}
			.fast.backward, .backward, .forward, .fast.forward { pointer-events: auto; }
			.fast.backward.disabled, .backward.disabled, .forward.disabled, .fast.forward.disabled { pointer-events: none; }
			#bottommenu {
				background-color: #333333;
				box-shadow: 0 0 10px 1px #333;
				padding: 10px;
			}
			.label, .value {
				color: white !important;
			}
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
		   	<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>

		<div class="ui container">
			<table id="tablehistory" class="ui very basic selectable table">
				<thead>
					<tr>
						<th></th>
						<th>Name</th>
						<th>Date</th>
						<th>Description</th>
					</tr>
				</thead>
				<tbody>
				%import ast
				%import time
				%import pretty
				%for row in rows:
					<tr class="selectable">
						<td class="collapsing">
						%if row['action'] == 0:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitle file has been erased." data-inverted="" data-position="top left">
								<i class="ui trash icon"></i>
							</div>
						%elif row['action'] == 1:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitle file has been downloaded." data-inverted="" data-position="top left">
								<i class="ui download icon"></i>
							</div>
						%elif row['action'] == 2:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitle file has been manually downloaded." data-inverted="" data-position="top left">
								<i class="ui user icon"></i>
							</div>
						%elif row['action'] == 3:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitle file has been upgraded." data-inverted="" data-position="top left">
								<i class="ui recycle icon"></i>
							</div>
						%elif row['action'] == 4:
							<div class="ui inverted basic compact icon" data-tooltip="Subtitle file has been manually uploaded." data-inverted="" data-position="top left">
								<i class="ui cloud upload icon"></i>
							</div>
						%end
						</td>
						<td>
							<a href="{{base_url}}movie/{{row['radarrId']}}">{{row['title']}}</a>
						</td>
						<td class="collapsing">
							<div class="ui inverted" data-tooltip="{{time.strftime('%Y/%m/%d %H:%M', time.localtime(row['timestamp']))}}" data-inverted="" data-position="top left">
								{{pretty.date(int(row['timestamp']))}}
							</div>
						</td>
						<td>
							% upgradable_criteria = dict([('timestamp', row['timestamp']), ('video_path', row['video_path']), ('score', row['score'])])
							% if upgradable_criteria in upgradable_movies:
							%     if row['languages'] != "None":
							%         desired_languages = ast.literal_eval(str(row['languages']))
							%         if row['forced'] == "True":
							%             forced_languages = [l + ":forced" for l in desired_languages]
							%         elif row['forced'] == "Both":
							%             forced_languages = [l + ":forced" for l in desired_languages] + desired_languages
							%         else:
							%             forced_languages = desired_languages
							%         end
							%         if row['languages'] and row['language'] and row['language'] in forced_languages:
										  <div class="ui inverted basic compact icon" data-tooltip="This Subtitle file is eligible for an upgrade." data-inverted="" data-position="top left">
										      <i class="ui green recycle icon upgrade"></i>{{row['description']}}
										  </div>
							%         else:
							              {{row['description']}}
							%         end
							%     end
							% else:
							      {{row['description']}}
							% end
						</td>
					</tr>
				%end
				</tbody>
			</table>
			%try: page_size
			%except NameError: page_size = "25"
			%end
			%if page_size != -1:
			<div class="ui grid">
				<div class="three column row">
			    	<div class="column"></div>
			    	<div class="center aligned column">
			    		<i class="\\
			    		%if page == '1':
			    		disabled\\
			    		%end
			    		 fast backward icon"></i>
			    		<i class="\\
			    		%if page == '1':
			    		disabled\\
			    		%end
			    		 backward icon"></i>
			    		{{page}} / {{max_page}}
			    		<i class="\\
			    		%if int(page) == int(max_page):
			    		disabled\\
			    		%end
			    		 forward icon"></i>
			    		<i class="\\
			    		%if int(page) == int(max_page):
			    		disabled\\
			    		%end
			    		 fast forward icon"></i>
			    	</div>
			    	<div class="right floated right aligned column">Total Records: {{row_count}}</div>
				</div>
			</div>
            %end
		</div>
		<div id='bottommenu' class="ui fluid inverted bottom fixed five item menu">
			<div class="ui small statistics">
				<div class="statistic">
			    	<div class="text value">
			    		<br>
			    		Movies
						<br>
						Statistics
			    	</div>
			    	<div class="label">
			    		
			    	</div>
			    </div>
			    <div class="statistic">
			    	<div class="value">
			    		{{stats[0]}}
			    	</div>
			    	<div class="label">
			    		In 24 Hours
			    	</div>
			    </div>
			    <div class="statistic">
			    	<div class="value">
			    		{{stats[1]}}
			    	</div>
			    	<div class="label">
			    		In One Week
			    	</div>
			    </div>
			    <div class="statistic">
			    	<div class="value">
			    		{{stats[2]}}
			    	</div>
			    	<div class="label">
			    		In One Year
		    		</div>
			    </div>
			    <div class="statistic">
			    	<div class="value">
			    		{{stats[3]}}
			    	</div>
			    	<div class="label">
			    		Total
			    	</div>
			    </div>
			</div>
		</div>

		<br><br><br><br>
	</body>
</html>


<script>
	if (sessionStorage.scrolly) {
	    $(window).scrollTop(sessionStorage.scrolly);
	    sessionStorage.clear();
	}

	$('a').on('click', function(){
		sessionStorage.scrolly=$(window).scrollTop();

		$('#loader').addClass('active');
	});

	$('.fast.backward').on('click', function(){
		loadURLmovies(1);
	});
	$('.backward:not(.fast)').on('click', function(){
		loadURLmovies({{int(page)-1}});
	});
	$('.forward:not(.fast)').on('click', function(){
		loadURLmovies({{int(page)+1}});
	});
	$('.fast.forward').on('click', function(){
		loadURLmovies({{int(max_page)}});
	});
</script>
