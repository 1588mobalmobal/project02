//모달 열기
function modal(id){
    $("#" + id).fadeIn()
  }
  
  //모달 닫기
  $('.modal-close').on('click', function(e){
    e.preventDefault();
    const modal = $(this).parents('.dialog');
    modal.fadeOut();
  });
  