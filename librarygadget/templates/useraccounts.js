
	$(".removeaccount").click(function(event) {
       event.preventDefault();
       var form = $(this).closest("form");
       form.submit();
    });



