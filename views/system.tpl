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
			#fondblanc {
				background-color: #ffffff;
				border-radius: 0px;
				box-shadow: 0px 0px 5px 5px #ffffff;
				margin-top: 32px;
				margin-bottom: 3em;
				padding: 1em;
			}
			#logs {
				margin-top: 4em;
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
		% include('menu.tpl')
			
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
				<div class="ui left floated basic buttons">
					<button id="refresh_log" class="ui button"><i class="refresh icon"></i>Refresh current page</button>
				</div>
				<div class="ui right floated basic buttons">
					<button id="download_log" class="ui button"><i class="download icon"></i>Download log file</button>
					<button id="empty_log" class="ui button"><i class="download icon"></i>Empty log file</button>
				</div>
				
				<div class="content">
					<div id="logs"></div>

					%try: page_size
					%except NameError: page_size = "25"
					%if page_size != -1:
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
                    %end
				</div>
			</div>
			<div class="ui bottom attached tab segment" data-tab="about">
				Bazarr version: {{bazarr_version}}
			</div>
		</div>
		% include('footer.tpl')
	</body>
</html>


<script>
	$('.menu .item')
		.tab()
	;

	function loadURL(page) {
		$.ajax({
	        url: "{{base_url}}logs/" + page,
	        beforeSend: function() { $('#loader').addClass('active'); },
        	complete: function() { $('#loader').removeClass('active'); },
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

	$('#refresh_log').click(function(){
		loadURL(current_page);
	})

	$('#download_log').click(function(){
		window.location = '{{base_url}}bazarr.log';
	})

	$('#empty_log').click(function(){
		window.location = '{{base_url}}emptylog';
	})

	$('.execute').click(function(){
		window.location = '{{base_url}}execute/' + $(this).data("taskid");
	})

	$('a:not(.tabs), button:not(.cancel, #download_log)').click(function(){
		$('#loader').addClass('active');
	})
</script>