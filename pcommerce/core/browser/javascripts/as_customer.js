jq('document').ready(function() {
    var parents = jq('#checkout .component:has(.as_customer)');
    parents.each(function(parent) {
      if(jq(parent).find('.as_customer').attr('checked'))
        jq(parent).find('.address').hide();
    });
    parents.find('.as_customer').click(function() {
      var checkbox = jq(this);
      var parent = jq(this);
      while(!parent.find('.address').size())
        parent = parent.parent();
      if ( checkbox.attr('checked') ) parent.find('.address').hide();
      else parent.find('.address').show();
    });
});