(function($) {
  $('document').ready(function() {
    var parents = $('#checkout .component:has(.as_customer)');
    parents.each(function() {
      if($(this).find('.as_customer').is(':checked'))
        $(this).find('.address').hide();
    });
    parents.find('.as_customer').click(function() {
      var checkbox = $(this);
      var parent = $(this);
      while(!parent.find('.address').size())
        parent = parent.parent();
      if(checkbox.is(':checked') )
        parent.find('.address').hide();
      else
        parent.find('.address').show();
    });
  });
})(jQuery);
