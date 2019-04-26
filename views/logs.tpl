<!DOCTYPE html>
<html lang="en">
	<head>
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
		<div id='logs_loader' class="ui page dimmer">
		   	<div id="loader_text" class="ui indeterminate text loader">Loading...</div>
		</div>
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
					<tr class='log' data-message="\\
%try:
{{line[3]}}\\
%except:
\\
%end
" data-exception="\\
%try:
{{line[4]}}\\
%except:
\\
%end
">
						<td class="collapsing"><i class="\\
%try:
%if line[1] == 'INFO    ':
blue info circle icon \\
%elif line[1] == 'WARNING ':
yellow warning circle icon \\
%elif line[1] == 'ERROR   ':
red bug icon \\
%elif line[1] == 'DEBUG   ':
bug icon \\
%end
%except:
%pass
%end
"></i></td>
						<td>\\
%try:
{{line[3]}}\\
%except:
\\
%end
</td>
						<td title="\\
%try:
{{line[0]}}" class="collapsing">{{pretty.date(int(time.mktime(datetime.datetime.strptime(line[0], "%d/%m/%Y %H:%M:%S").timetuple())))}}</td>
%except:
" class="collapsing"></td>
%end
					</tr>
				%end
				</tbody>
			</table>
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
	</body>
</html>

<script>
	$('.modal')
		.modal({
	    	autofocus: false
		});

	$('.log').on('click', function(){
		$("#message").html($(this).data("message"));
        let exception = $(this).data("exception");
		exception = exception.replace(/'/g,"");
        exception = exception.replace(/\\n\s\s\s\s/g, "\\n&emsp;&emsp;");
		exception = exception.replace(/\\n\s\s/g, "\\n&emsp;");
		exception = exception.replace(/\\n/g, "<br />");
		$("#exception").html(exception);
		$('#modal').modal('show');
	});
</script>