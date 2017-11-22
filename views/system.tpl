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
		
		<title>System - Bazarr</title>
		
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
				padding: 1em;
			}
			.fast.backward, .backward, .forward, .fast.forward {
    			cursor: pointer;
			}
			.fast.backward, .backward, .forward, .fast.forward { pointer-events: auto; }
			.fast.backward.disabled, .backward.disabled, .forward.disabled, .fast.forward.disabled { pointer-events: none; }
		</style>
	</head>
	<body>
		<div id='loader' class="ui page dimmer">
		   	<div class="ui indeterminate text loader">Loading...</div>
		</div>
		<div id="divmenu" class="ui container">
			<div style="background-color:#272727;" class="ui inverted borderless labeled icon huge menu five item">
				<a href="{{base_url}}"><img style="margin-right:32px;" class="logo" src="{{base_url}}static/logo128.png"></a>
				<div style="height:80px;" class="ui container">
					<a class="item" href="{{base_url}}">
						<i class="play icon"></i>
						Series
					</a>
					<a class="item" href="{{base_url}}history">
						<i class="wait icon"></i>
						History
					</a>
					<a class="item" href="{{base_url}}wanted">
						<i class="warning sign icon"></i>
						Wanted
					</a>
					<a class="item" href="{{base_url}}settings">
						<i class="settings icon"></i>
						Settings
					</a>
					<a class="item" href="{{base_url}}system">
						<i class="laptop icon"></i>
						System
					</a>
				</div>
			</div>
		</div>
			
		<div id="fondblanc" class="ui container">
			<div class="ui top attached tabular menu">
				<a class="tabs item active" data-tab="tasks">Tasks</a>
				<a class="tabs item" data-tab="logs">Logs</a>
				<a class="tabs item" data-tab="about">About</a>
			</div>
			<div class="ui bottom attached tab segment active" data-tab="tasks">
				<div class="content">
					<table class="ui very basic selectable table">
						<thead>
							<tr>
								<th>Name</th>
								<th>Execution Frequency</th>
								<th>Next Execution</th>
								<th class="collapsing"></th>
							</tr>
						</thead>
						<tbody>
						%for task in task_list:
							<tr>
								<td>{{task[0]}}</td>
								<td>{{task[1]}}</td>
								<td>{{task[2]}}</td>
								<td class="collapsing">
									<div class="execute ui inverted basic compact icon" data-tooltip="Execute {{task[0]}}" data-inverted="" data-taskid='{{task[3]}}'>
										<i class="ui black refresh icon"></i>
									</div>
								</td>
							</tr>
						%end
						</tbody>
					</table>
				</div>
			</div>
			<div class="ui bottom attached tab segment" data-tab="logs">
				<div class="content">
					<div id="logs"></div>

					<div class="ui grid">
						<div class="three column row">
					    	<div class="column"></div>
					    	<div class="center aligned column">
					    		<i class="fast backward icon"></i>
					    		<i class="backward icon"></i>
					    		<span id="page"></span> / {{max_page}}
					    		<i class="forward icon"></i>
					    		<i class="fast forward icon"></i>
					    	</div>
					    	<div class="right floated right aligned column">Total records: {{row_count}}</div>
						</div>
					</div>
				</div>
			</div>
			<div class="ui bottom attached tab segment" data-tab="about">
				Bazarr version: {{bazarr_version}}
			</div>
		</div>
	</body>
</html>


<script>
	$('.menu .item')
		.tab()
	;

	function loadURL(page) {
		$.ajax({
	        url: "{{base_url}}logs/" + page,
	        cache: false
	    }).done(function(data) {
	    	$("#logs").html(data);
	    });

	    current_page = page;
	    
	    $("#page").text(current_page);
	    if (current_page == 1) {
	    	$(".backward, .fast.backward").addClass("disabled");
	    }
	    if (current_page == {{int(max_page)}}) {
	    	$(".forward, .fast.forward").addClass("disabled");
	    }
	    if (current_page > 1 && current_page < {{int(max_page)}}) {
	    	$(".backward, .fast.backward").removeClass("disabled");
	    	$(".forward, .fast.forward").removeClass("disabled");
	    }
	}

	loadURL(1);

	$('.backward').click(function(){
		loadURL(current_page - 1);
	})
	$('.fast.backward').click(function(){
		loadURL(1);
	})
	$('.forward').click(function(){
		loadURL(current_page + 1);
	})
	$('.fast.forward').click(function(){
		loadURL({{int(max_page)}});
	})

	$('.execute').click(function(){
		window.location = '{{base_url}}execute/' + $(this).data("taskid");
	})

	$('a:not(.tabs), button:not(.cancel)').click(function(){
		$('#loader').addClass('active');
	})
</script>