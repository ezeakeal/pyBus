$(document).ready(function() {
  function displayPlaying(status){
    status=JSON.parse(status);

    var trackStatus = status['track'];
    var daemonStatus = status['status'];
    var customStatus = status['custom'];

    var daemonState = daemonStatus['state'];
    
    if (daemonState != "stop"){
      var timeInfo = daemonStatus['time'].split(':');
      var timePerc = timeInfo[0]/timeInfo[1]*100
      var timeString = timeInfo[0] +' of '+timeInfo[1]+' seconds';
    }
    else {
      timeString = "-- stopped --"
      timePerc = 0;
    }

    statusHTML = [
      '<h4>Now Playing:</h4>',
      '<hr>',
      '<table class="table table-condensed">',
      '<tr><td><strong>Artist:</strong></td> <td>'+trackStatus['artist'] +'</td></tr>',
      '<tr><td><strong>Album:</strong></td>  <td>'+trackStatus['album'] +'</td></tr>',
      '<tr><td><strong>Title:</strong></td>  <td>'+trackStatus['title'] +'</td></tr>',
      '<tr><td><strong>Time:</strong></td>  <td>'+timeString+'</td></tr>',
      '</table>'
    ].join(' ');
    $('#progressbar_track').css('width',timePerc+'%');

    $('#currentPlaying').html(statusHTML);

    if (customStatus){
      var speed = customStatus['speed'];
      var revs = customStatus['revs'];
      var maxRevs = 60;
      var maxSpeed = 160;

      var revsPerc = revs/maxRevs*100;
      var speedPerc = speed/maxSpeed*100;

      $('#progressbar_speed').css('width',speedPerc+'%');
      $('#progressbar_revs').css('width',revsPerc+'%');

      $('#carStatus').find('td[name="revsval"]').html((revs*100) + ' RPM');
      $('#carStatus').find('td[name="speedval"]').html((speed) + ' KM/H');
    }
  }

  // ###################################
  // POLL FOR SONG STATUS
  // ###################################
  window.pollStatus=function (callback) {
    var remoteInterval = setInterval(function() {
      $.ajax({
        type: 'GET',
        url: "/musicStatus",
        success:function(data, textStatus, jqXHR) {
          var status = jqXHR.responseText;
          displayPlaying(status);
        }
      });
    }, 1000 );
  }


  function addSongToLibraryTable(song){
    tableBody = $('#mediaList').find('tbody');
    songData = Object.keys(song);

    songFields = [
      "artist", "genre", "title", "file"
    ]
    for (var i = 0; i < songFields.length; i++){
      field = songFields[i];
      if (songData.indexOf(field) == -1){
        return false;
      }
    }

    insertHTML=[
      '<tr>',
      '<td class="sorting_1">'+song['artist']+'</td>',
      '<td class="">'+song['album']+'</td>',
      '<td class="center">'+song['genre']+'</td>',
      '<td class="center">'+song['title']+'</td>',
      '<td class="center btn-group" filepath="'+song['file']+'" name="mediaLibrary_actionButtons">',
        '<button plist_action="add" class="btn btn-info"><i class="icon-plus-sign icon-white"></i></button>',
        '<button plist_action="play" class="btn btn-success"><i class="icon-play icon-white"></i></button>',
      '</td>',
      '</tr>'
    ].join(' ');

    tableBody.append(insertHTML);
  }
  function addSongToPlaylistTable(song){
    if (song){
      tableBody = $('#playList').find('tbody');
      songData = Object.keys(song);

      songFields = [
        "artist", "genre", "title", "file"
      ]
      for (var i = 0; i < songFields.length; i++){
        field = songFields[i];
        if (songData.indexOf(field) == -1){
          return false;
        }
      }

      insertHTML=[
        '<tr>',
        '<td class="sorting_1">'+song['artist']+'</td>',
        '<td class="">'+song['album']+'</td>',
        '<td class="center">'+song['genre']+'</td>',
        '<td class="center">'+song['title']+'</td>',
        '<td class="center btn-group" filepath="'+song['file']+'" name="playList_actionButtons">',
          '<button plist_action="play" class="btn btn-success"><i class="icon-play icon-white"></i></button>',
          '<button plist_action="remove" class="btn btn-danger"><i class="icon-remove-sign icon-white"></i></button>',
        '</td>',
        '</tr>'
      ].join(' ');

      tableBody.append(insertHTML);
    }
  }

  function modLibary(filepath, type){
    var getData = {
      "type" : type,
      "path" : filepath
    };

    $.ajax({
      type: 'GET',
      data: getData,
      url: "/playlistMod"
    });
  }

  function renderLibrary(tableHTML, completed_callback){
    // var interval = setInterval( function() { // Generate table in sections. Use setInterval to allow browser time to render
    //   var song = library[i_Key];
      
    //   addSongToLibraryTable(song);

    //   i_Key++; 
    //   if( i_Key >= library.length){
    //   //if( i_Key >= 15){
    //     clearInterval(interval);
    //     completed_callback();
    //   }
    // }, 10);
    tableBody = $('#mediaList').find('tbody');
    tableBody.html(tableHTML)
    completed_callback();
  }

  function renderPlaylist(tableHTML, completed_callback){
    // var interval = setInterval( function() { // Generate table in sections. Use setInterval to allow browser time to render
    //   var song = library[i_Key];
      
    //   addSongToPlaylistTable(song);

    //   i_Key++; 
    //   if( i_Key >= library.length){
    //   //if( i_Key >= 15){
    //     clearInterval(interval);
    //     completed_callback();
    //   }
    // }, 10);
    tableBody = $('#playList').find('tbody');
    tableBody.html(tableHTML)
    completed_callback();
  }

  window.enableTabs=function(){
    $('#mediaLibrary').find('.nav-tabs').find('li').click(function (e) {
      e.preventDefault();
      $(this).tab('show');
    });
  }

  window.addSongToPlaylist=function(data, filePath){
    var playlist = $('#playList').dataTable();
    var library = $('#mediaList').dataTable();

    var select = data.parent().parent()[0];
    var rowData = library.fnGetData(select);    
    rowData[4] = "Reconstruct"
    playlist.fnAddData(rowData);
    var reconstructElement = playlist.find('td:contains("Reconstruct")');
    var reconstructHTML = [
      '<button plist_action="play" class="btn btn-success"><i class="icon-play icon-white"></i></button>',
      '<button plist_action="remove" class="btn btn-danger"><i class="icon-remove-sign icon-white"></i></button>'
    ].join(' ');
    reconstructElement.attr("filepath", filePath);
    reconstructElement.attr("name", "playList_actionButtons");
    reconstructElement.html(reconstructHTML);
    reconstructElement.find('button').click(function(){
      var filePath = $(this).parent().attr('filepath');
      var fileAction = $(this).attr('plist_action');
      modLibary(filePath, fileAction);
      if (fileAction == "remove"){
        removeSongFromPlaylist($(this));
      }
    });
  }

  window.removeSongFromPlaylist=function(data){
    var playlist = $('#playList').dataTable();
    var select = data.parent().parent()[0];
    var rowInd = playlist.fnGetPosition(select);    
    playlist.fnDeleteRow( rowInd );
  }


  window.renderLibraryTable=function(){
    $.ajax({
      type: 'GET',
      url: "/getLibrary",
      success:function(libraryHTML, textStatus, jqXHR) {
        renderLibrary(libraryHTML, function(){
          $('td[name="mediaLibrary_actionButtons"]').find('button').click(function(){
            var filePath = $(this).parent().attr('filepath');
            var fileAction = $(this).attr('plist_action');
            modLibary(filePath, fileAction);
            if (fileAction == "add"){
              addSongToPlaylist($(this), filePath);
            }
          });
          $('#mediaList').dataTable({
            "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>",
            "sPaginationType": "bootstrap"
          });
          $.extend( $.fn.dataTableExt.oStdClasses, {
              "sWrapper": "dataTables_wrapper form-inline"
          });
          $('#media_loading').hide();
          $('#mediaList').show();
        });
      }
    });
  }
  window.renderPlaylistTable=function(){
    $.ajax({
      type: 'GET',
      url: "/getPlaylist",
      success:function(playlistHTML, textStatus, jqXHR) {
        renderPlaylist(playlistHTML, function(){
          $('td[name="playList_actionButtons"]').find('button').click(function(){
            var filePath = $(this).parent().attr('filepath');
            var fileAction = $(this).attr('plist_action');
            modLibary(filePath, fileAction);
            if (fileAction == "remove"){
              removeSongFromPlaylist($(this));
            }
          });
          $('#playList').dataTable({
            "sDom": "<'row-fluid'<'span6'l><'span6'f>r>t<'row-fluid'<'span6'i><'span6'p>>",
            "sPaginationType": "bootstrap"
          });
          $.extend( $.fn.dataTableExt.oStdClasses, {
              "sWrapper": "dataTables_wrapper form-inline"
          });
          $('#play_loading').hide();
          $('#playList').show();
        });
      }
    });
  }

  function enableControls(){
    $('[mediaAction]').click(function(){
      modLibary("", $(this).attr('mediaAction'))
    });
  }

  enableTabs();
  enableControls();
  renderLibraryTable();
  renderPlaylistTable();
  pollStatus();
  
} );

