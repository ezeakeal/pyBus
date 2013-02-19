$(document).ready(function() {
   window.buildSysManage();
});

function buildSys_Supervisor(success_cb){
  $.ajax({
    type: 'GET',
    url: "/supervisor/getSupStatus",
    success:function(data, textStatus, jqXHR) {
      var supStatus = JSON.parse(data);
      $('#sys_manage_supervisor').append([ 
        '<table class="table"><tbody>',
        '<tr><td><h4>SupervisorD</h4></td><td>',
        "<span class='label label-success'><h4>"+supStatus['statename']+"</h4></span>",
        '</td></tr></tbody></table>'
      ].join("\n"));
      success_cb()
    }
  });
}

function buildSys_Proc(){
  $.ajax({
    type: 'GET',
    url: "/supervisor/getProcStatus",
    success:function(data, textStatus, jqXHR) {
      var allProcStatus = JSON.parse(data);
      procHTMLBlock = [];
      procHTMLBlock = procHTMLBlock.concat([ 
        "<table class='table'><thead><tr>",
        "<th>ProcName</th>",
        "<th>Description</th>",
        "<th>Status</th>",
        "<th>Action</th>",
        "</tr></thead><tbody>"
      ]);
      for (pInd in allProcStatus){
        procStatus = allProcStatus[pInd];
        procHTMLBlock = procHTMLBlock.concat([ 
          "<tr name='procRow' proc='"+procStatus['name']+"'>",
          "<td>"+procStatus['name']+"</td>",
          "<td>"+procStatus['description']+"</td>"
        ])
        var labelClass = "label-success"
        if (procStatus['statename'] != "RUNNING") { labelClass = "label-important" }
        procHTMLBlock = procHTMLBlock.concat([  
          "<td><span class='label "+labelClass+"'>"+procStatus['statename']+"</span></td>",
          '<td><a class="btn" action="procStart"><i class="icon-play"></i></a><a class="btn" action="procStop"><i class="icon-stop"></i></a><a class="btn" action="procTail"><i class="icon-eye-open"></i></a></td>',
          "<td></td>",
          '</tr>'
        ]);
      }
      procHTMLBlock = procHTMLBlock.concat([  
        '</tbody></table>'
      ]);
      $('#sys_manage_proc').html(procHTMLBlock.join('\n'));
      window.buildSys_ProcBindButton(allProcStatus);
    }
  });
}

function startProc(procName){
  $.ajax({
    type: 'GET',
    data: {"proc": procName},
    url: "/supervisor/startSupProc",
    success:function(data, textStatus, jqXHR) {
      window.buildSys_Proc();
    }
  });
}

function stopProc(procName){
  $.ajax({
    type: 'GET',
    data: {"proc": procName},
    url: "/supervisor/stopSupProc",
    success:function(data, textStatus, jqXHR) {
      window.buildSys_Proc();
    }
  });
}

function clearProcLog(procName){
  $.ajax({
    type: 'GET',
    data: {"proc": procName},
    url: "/supervisor/clearProcLog",
    success:function(data, textStatus, jqXHR) {

    }
  });
}

function tailProc(procName){
  if (window.sup_tail_log == null){
    window.clearProcLog(procName);
    window.sup_tail_log_length = 0;
    $('#logOutput_pre').html("");
    window.sup_tail_log = setInterval(function() {
      $.ajax({
        type: 'GET',
        data: {"proc": procName, "offset": window.sup_tail_log_length, "length": window.sup_tail_log_length+10240},
        url: "/supervisor/tailSupProc",
        success:function(data, textStatus, jqXHR) {
          logData = JSON.parse(data);
          window.sup_tail_log_length = logData[1] - window.sup_tail_log_length;
          $('#logOutput_pre').html(logData[0]);
        }
      });
    }, 1000);
  } else {
    clearInterval(window.sup_tail_log);
    window.buildSys_Proc();
    window.sup_tail_log = null;
  }
}

function buildSys_ProcBindButton(allProcStatus){
  $("tr[name='procRow']").each(function ( index, domEle) {
    var procName = $(domEle).attr('proc');
    $( domEle ).find("a[action='procStart']").click(function(){
      var $this = $(this);
      $this.text('...');
      window.startProc(procName);
    });
    $( domEle ).find("a[action='procStop']").click(function(){
      var $this = $(this);
      $this.text('...');
      window.stopProc(procName);
    });
    $( domEle ).find("a[action='procTail']").click(function(){
      var $this = $(this);
      $this.addClass("btn btn-warning");
      window.tailProc(procName);
    });
  });
}

function buildSysManage(){
  window.buildSys_Supervisor(window.buildSys_Proc);
}