<html lang="en">
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
				border-radius: 0;
				box-shadow: 0 0 5px 5px #ffffff;
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
		   	<div id='loader_text' class="ui indeterminate text loader">Loading...</div>
		</div>
		% include('menu.tpl')
			
		<div id="fondblanc" class="ui container">
			<div class="ui basic icon buttons" style="float: right;">
				<div id="shutdown" class="ui icon button" data-tooltip="Shutdown" data-inverted=""><i class="red power off icon"></i></div>
				<div id="restart" class="ui icon button" data-tooltip="Restart" data-inverted=""><i class="redo alternate icon"></i></div>
                % from config import settings
                % if settings.auth.type != "None":
                    <div id="logout" class="ui icon button" data-tooltip="Logout" data-inverted=""><i class="sign-out icon"></i></div>
                % end
			</div>
			% import datetime
            % throttled_providers_count = len(eval(str(settings.general.throtteled_providers)))
            <div class="ui top attached tabular menu">
				<a class="tabs item active" data-tab="tasks">Tasks</a>
				<a class="tabs item" data-tab="logs">Logs</a>
                <a class="tabs item" data-tab="providers">Providers
                    % if throttled_providers_count:
                    <div class="ui tiny yellow label">
                        {{throttled_providers_count}}
                    </div>
                    % end
                </a>
                <a class="tabs item" data-tab="status">Status</a>
				<a class="tabs item" data-tab="releases">Releases</a>
			</div>
			<div class="ui bottom attached tab segment active" data-tab="tasks">
				<div class="content">
					<table class="ui very basic selectable table" id="tasks">
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
							<tr id="{{task[3]}}">
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

                <label>Log level filter:</label>
                    <select name="level" id="level" class="ui floated selection dropdown">
                        <option value="ALL">All</option>
                        <option value="WARNING">WARNING</option>
                        <option value="INFO">INFO</option>
                        <option value="ERROR">ERROR</option>
                        <option value="DEBUG">DEBUG</option>
                    </select>

				
				<div class="content">
					<div id="logs"></div>

					%try: page_size
					%except NameError: page_size = "25"
					%end
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
            <div class="ui bottom attached tab segment" data-tab="providers">
				<div class="content">
					<table class="ui very basic table">
						<thead>
							<tr>
								<th>Name</th>
								<th>Status</th>
								<th>Next retry</th>
							</tr>
						</thead>
						<tbody>
						%for provider in throttled_providers:
							<tr>
								<td>{{provider[0]}}</td>
								<td>{{provider[1] if provider[1] is not None else "Good"}}</td>
								<td>{{provider[2] if provider[2] is not "now" else "-"}}</td>
							</tr>
						%end
						</tbody>
					</table>
				</div>
			</div>
            <div class="ui bottom attached tab segment" data-tab="status">
				<div class="ui dividing header">About</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Bazarr version</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{bazarr_version}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        % if settings.general.getboolean('use_sonarr'):
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Sonarr version</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{sonarr_version}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        % end
                        % if settings.general.getboolean('use_radarr'):
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Radarr version</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{radarr_version}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        % end
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Operating system</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{operating_system}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Python version</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{python_version}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Bazarr directory</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{bazarr_dir}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Bazarr config directory</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        {{config_dir}}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="ui dividing header">More info</div>
                <div class="twelve wide column">
                    <div class="ui grid">
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Source</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <i class="github icon"></i><a href="https://github.com/morpheus65535/bazarr" target="_blank">Bazarr on GitHub</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Wiki</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <i class="wikipedia w icon"></i><a href="https://github.com/morpheus65535/bazarr/wiki" target="_blank">Bazarr Wiki</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Discord</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <i class="discord icon"></i><a href="https://discord.gg/MH2e2eb" target="_blank">Bazarr on Discord</a>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
			</div>

			<div class="ui bottom attached tab segment" data-tab="releases">
				%for release in releases:
				<h2 class="ui header">
					%if release[0][1:] == bazarr_version:
					{{release[0]}} <div class="ui green label">Current version</div>
					%else:
					{{release[0]}}
					%end
				</h2>
				<div class="ui list">
					%release_lines = release[1].split('\r\n')
					%for i, release_line in enumerate(release_lines):
					%if i == 0:
					<div class="item">
						<div><h4>{{release_line}}</h4></div>
						<div class="list">
					%else:
							<div class="item">{{release_line}}</div>
					%end
					%end
						</div>
					</div>
				</div>
				%end
			</div>
		</div>
		% include('footer.tpl')
	</body>
</html>


<script>
	$('.menu .item')
		.tab();

	function loadURL(level, page) {
		$.ajax({
	        url: "{{base_url}}logs/" + level + "/" + page,
	        beforeSend: function() { $('#loader').addClass('active'); },
        	complete: function() { $('#loader').removeClass('active'); },
	        cache: false
	    }).done(function(data) {
	    	$("#logs").html(data);
	    });

	    current_page = page;
	    $('#level').on('change', function() {
            current_level = $('#level option:checked').val();
        });

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

	loadURL('ALL', 1);

	$('.backward').on('click', function(){
		loadURL(current_level, current_page - 1);
	});
	$('.fast.backward').on('click', function(){
		loadURL(current_level, 1);
	});
	$('.forward').on('click', function(){
		loadURL(current_level, current_page + 1);
	});
	$('.fast.forward').on('click', function(){
		loadURL(current_level, {{int(max_page)}});
	});

	$('#refresh_log').on('click', function(){
		loadURL(current_level, current_page);
	});

	$('#level').on('change', function(){
		loadURL(current_level, current_page);
	});

	$('#download_log').on('click', function(){
		window.location = '{{base_url}}bazarr.log';
	});

	$('#empty_log').on('click', function(){
		window.location = '{{base_url}}emptylog';
	});

	$('.execute').on('click', function(){
	    $(this).addClass('disabled');
		$(this).find('i:first').addClass('loading');
	    $.ajax({
            url: '{{base_url}}execute/' + $(this).data("taskid")
        })
	});

	$('a:not(.tabs), button:not(.cancel, #download_log), #restart').on('click', function(){
		$('#loader').addClass('active');
	});

    $('a[target="_blank"]').on('click', function(){
        $('#loader').removeClass('active');
    });

	$('#shutdown').on('click', function(){
		$.ajax({
			url: "{{base_url}}shutdown",
			async: false
		})
		.always(function(){
			document.open();
			document.write('Bazarr has shutdown.');
			document.close();
		});
	});

    $('#logout').on('click', function(){
		window.location = '{{base_url}}logout';
	});

	$('#restart').on('click', function(){
		$('#loader_text').text("Bazarr is restarting, please wait...");
		$.ajax({
			url: "{{base_url}}restart",
			async: true
		})
		.done(function(){
    		setTimeout(function(){ setInterval(ping, 2000); },8000);
		})
	});

    % from config import settings
    % from get_args import args
	% ip = settings.general.ip
	% port = args.port if args.port else settings.general.port
	% base_url = settings.general.base_url

	if ("{{ip}}" === "0.0.0.0") {
		public_ip = window.location.hostname;
	} else {
		public_ip = "{{ip}}";
	}

	protocol = window.location.protocol;

	if (window.location.port === '{{current_port}}') {
	    public_port = '{{port}}';
    } else {
        public_port = window.location.port;
    }

	function ping() {
		$.ajax({
			url: protocol + '//' + public_ip + ':' + public_port + '{{base_url}}',
			success: function(result) {
				window.location.href= protocol + '//' + public_ip + ':' + public_port + '{{base_url}}';
			}
		});
	}
</script>