jq('document').ready(function() {
    var parents = jq('#checkout .component:has(.as_customer)');
    parents.each(function() {
      if(jq(this).find('.as_customer').is(':checked'))
        jq(this).find('.address').hide();
    });
    parents.find('.as_customer').click(function() {
      var checkbox = jq(this);
      var parent = jq(this);
      while(!parent.find('.address').size())
        parent = parent.parent();
      if ( checkbox.is(':checked') )
        parent.find('.address').hide();
      else
        parent.find('.address').show();
    });
});