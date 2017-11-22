<html>
	<head>
		<!DOCTYPE html>
		<script src="{{base_url}}static/jquery/jquery-latest.min.js"></script>
		<script src="{{base_url}}static/semantic/semantic.min.js"></script>
		<script src="{{base_url}}static/jquery/tablesort.js"></script>
		<link rel="stylesheet" href="{{base_url}}static/semantic/semantic.min.css">

		<style>
			body {
				background-color: #272727;
			}
		</style>
	</head>
	<body>
		<div class="content">
			<table class="ui very basic selectable table">
				<thead>
					<tr>
						<th class="collapsing"></th>
						<th>Message</th>
						<th class="collapsing">Time</th>
					</tr>
				</thead>
				<tbody>
				%import time
				%import datetime
				%import pretty
				%for log in logs:
					%line = []
					%line = log.split('|')
					<tr class='log' data-message='{{line[2]}}' data-exception='{{line[3].replace("\\n", "<br />")}}'>
						<td class="collapsing"><i class="\\
						%if line[1] == 'INFO':
blue info circle \\
						%elif line[1] == 'WARNING':
yellow warning circle \\
						%elif line[1] == 'ERROR':
red bug \\
						%end
icon"></i></td>
						<td>{{line[2]}}</td>
						<td title='{{line[0]}}' class="collapsing">{{pretty.date(int(time.mktime(datetime.datetime.strptime(line[0], "%d/%m/%Y %H:%M:%S").timetuple())))}}</td>
					</tr>
				%end
				</tbody>
			</table>
		</div>

		<div class="ui small modal">
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
	</body>
</html>

<script>
	$('.modal')
		.modal({
	    	autofocus: false
		})
	;

	$('.log').click(function(){
		$("#message").html($(this).data("message"));
		$("#exception").html($(this).data("exception"));
		$('.small.modal').modal('show');
	})
</script>