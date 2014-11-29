$(document).ready(function() {

  function modLibary(filepath, type){
    $.ajax({
      type: 'GET',
      url: "/mediaCommand/" + type + "/" + filepath
    });
  }

  function bindFunctionTable(){
    $('td[name="actionButtons"]').find('button').click(function(){
      var filePath = $(this).parent().attr('filepath');
      var fileAction = $(this).attr('plistaction');
      modLibary(filePath, fileAction);
    });
  }

  function createDataTable(){
    $('#playList').dataTable();
  }

  bindFunctionTable();
  createDataTable();
  
} );

