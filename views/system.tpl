<!DOCTYPE html>
<html lang="en">
	<head>
		<script src="{{base_url}}static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}static/semantic/semantic.min.js"></script>
		<script src="{{base_url}}static/jquery/tablesort.js"></script>
		<script src="{{base_url}}static/datatables/jquery.dataTables.min.js"></script>
		<script src="{{base_url}}static/datatables/dataTables.semanticui.min.js"></script>
		<script src="{{base_url}}static/moment/moment.js"></script>
		<link rel="stylesheet" href="{{base_url}}static/semantic/semantic.min.css">
		<link rel="stylesheet" type="text/css" href="{{base_url}}static/datatables/datatables.min.css"/>
		<link rel="stylesheet" type="text/css" href="{{base_url}}static/datatables/semanticui.min.css"/>
		
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
			.fast.backward, .backward, .forward, .fast.forward {
    			cursor: pointer;
			}
			.fast.backward, .backward, .forward, .fast.forward { pointer-events: auto; }
			.fast.backward.disabled, .backward.disabled, .forward.disabled, .fast.forward.disabled { pointer-events: none; }
            .dataTables_filter{
               display:none;
            }
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

                <div class="ui two column grid container">
                    <div class="row">
                        <div class="left floatedcolumn">
                            <div class="ui basic buttons">
                                <button id="refresh_log" class="ui button"><i class="refresh icon"></i>Refresh Current Page</button>
                                <button id="download_log" class="ui button"><i class="download icon"></i>Download Log File</button>
                                <button id="empty_log" class="ui button"><i class="trash icon"></i>Empty Log</button>
                            </div>
                        </div>
                        <div class="right floated right aligned column">
                            <div class="ui basic icon buttons">
                                <button class="ui active button filter_log" id="all_log" data-level="ALL" data-tooltip="All"><i class="circle outline icon"></i></button>
                                <button class="ui button filter_log" id="info_log" data-level="INFO" data-tooltip="Info"><i class="blue info circle icon"></i></button>
                                <button class="ui button filter_log" id="warning_log" data-level="WARNING" data-tooltip="Warning"><i class="yellow warning circle icon"></i></button>
                                <button class="ui button filter_log" id="error_log" data-level="ERROR" data-tooltip="Error"><i class="red bug icon"></i></button>
                                <button class="ui button filter_log" id="debug_log" data-level="DEBUG" data-tooltip="Debug"><i class="black bug icon"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
				
				<div class="content">
					<table id="logs" class="display" style="width:100%">
                        <thead>
                            <tr>
                                <th></th>
                                <th class="collapsing"></th>
                                <th style="text-align: left;">Message:</th>
                                <th class="collapsing" style="text-align: left;">Time:</th>
                                <th></th>
                            </tr>
                        </thead>
                    </table>
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
                                <label>Bazarr Version:</label>
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
                                <label>Sonarr Version:</label>
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
                                <label>Radarr Version:</label>
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
                                <label>Operating System:</label>
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
                                <label>Python Version:</label>
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
                                <label>Bazarr Directory:</label>
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
                                <label>Bazarr Config Directory:</label>
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
                                <label>Home Page:</label>
                            </div>
                            <div class="five wide column">
                                <div class='field'>
                                    <div class="ui fluid input">
                                        <i class="paper plane icon"></i><a href="https://www.bazarr.media" target="_blank">Bazarr Website</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="middle aligned row">
                            <div class="right aligned four wide column">
                                <label>Source:</label>
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
                                <label>Wiki:</label>
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
                                <label>Discord:</label>
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
					{{release[0]}} <div class="ui green label">Current Version</div>
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

        <div id="modal" class="ui small modal">
			<i class="close icon"></i>
			<div class="header">
				<div>Details</div>
			</div>
			<div class="content">
				Message
				<div id='message' class="ui segment">
					<p></p>
				</div>
				Exception
				<div id='exception' class="ui segment">
					<p></p>
				</div>
			</div>
			<div class="actions">
				<button class="ui cancel button" >Close</button>
			</div>
		</div>

		% include('footer.tpl')
	</body>
</html>


<script>
	$('.modal')
		.modal({
	    	autofocus: false
		});

    $('.menu .item')
		.tab();

	$('#refresh_log').on('click', function(){
		table.ajax.reload();
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

	$('a:not(.tabs), button:not(.cancel, #download_log, .filter_log, #refresh_log), #restart').on('click', function(){
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

	var table = $('#logs').DataTable( {
		    destroy: true,
		    language: {
				loadingRecords: '<br><div class="ui active inverted dimmer" style="width: 95%;"><div class="ui centered inline loader"></div></div><br>',
				zeroRecords: 'No entries found in logs matching this log level.'
		    },
		    paging: true,
			lengthChange: false,
			pageLength: {{page_size}},
    		searching: true,
            search: {
                regex: true
            },
    		ordering: false,
    		processing: false,
        	serverSide: false,
        	ajax: {
				url: '{{base_url}}logs',
				dataSrc: 'data'
			},
			drawCallback: function(settings) {
                $('.inline.dropdown').dropdown();
			},
			columns: [
                {
                    data: 1,
                    render: function (data, type, row) {
                        return $.trim(data);
                    }
                },
			    { data: 1,
				render: function ( data, type, row ) {
        			var icon;
        			switch ($.trim(data)) {
                        case 'INFO':
                            icon = 'blue info circle icon';
                            break;
                        case 'WARNING':
                            icon = 'yellow warning circle icon';
                            break;
                        case 'ERROR':
                            icon = 'red bug icon';
                            break;
                        case 'DEBUG':
                            icon = 'black bug icon';
                    }
				    return '<i class="' + icon + '"></i>';
    				}
                },
                { data: 3,
				render: function ( data, type, row ) {
        			return $.trim(data);
    				}
                },
                { data: 0,
				render: function ( data, type, row ) {
        			return '<div class="description" data-tooltip="' + $.trim(data) + '" data-inverted="" data-position="top left">' + moment($.trim(data), "DD/MM/YYYY hh:mm:ss").fromNow() + '</div>'
                    }
                },
                { data: 4,
				render: function ( data, type, row ) {
        			return $.trim(data);
    				}
                }
            ],
            columnDefs: [
                {
                    "targets": [ 0 ],
                    "visible": false,
                    "searchable": true
                },
                {
                    "targets": [ 4 ],
                    "visible": false,
                    "searchable": false
                }
			]
		} );

	$('.filter_log').on( 'click', function () {
	    $('.filter_log').removeClass('active');
	    $(this).addClass('active');
	    if ( $(this).data('level') === 'INFO') {
	        table.column( 0 ).search( 'INFO|WARNING|ERROR|DEBUG', true, false).draw();
        } else if ( $(this).data('level') === 'WARNING') {
	        table.column( 0 ).search( 'WARNING|ERROR|DEBUG', true, false ).draw();
        } else if ( $(this).data('level') === 'ERROR') {
	        table.column( 0 ).search( 'ERROR|DEBUG', true, false ).draw();
        } else if ( $(this).data('level') === 'DEBUG') {
	        table.column( 0 ).search( 'DEBUG', true, false ).draw();
        } else if ( $(this).data('level') === 'ALL') {
            table.column(0).search('').draw();
        }
    } );

	$('#logs').on('click', 'tr', function(event) {
        var data = table.row( this ).data();

        $("#message").html(data[3]);
        let exception = data[4];
		exception = exception.replace(/'/g,"");
        exception = exception.replace(/\\n\s\s\s\s/g, "\\n&emsp;&emsp;");
		exception = exception.replace(/\\n\s\s/g, "\\n&emsp;");
		exception = exception.replace(/\\n/g, "<br />");
		$("#exception").html(exception);
		$('#modal').modal('show');
    });
</script>
