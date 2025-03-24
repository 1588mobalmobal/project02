document.addEventListener('DOMContentLoaded', function() {
    const diaryDate = document.getElementById('diaryDate');
    const diaryContent = document.getElementById('diaryContent');
    const saveButton = document.getElementById('saveButton');
  
  // 오늘 날짜를 YYYY-MM-DD 형식으로 가져오기
    function getTodayDate() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }
  
    // 로컬 스토리지에서 일기 목록 불러오기 ??
    let diaries = JSON.parse(localStorage.getItem('diaries')) || [];
  
    diaryDate.value=getTodayDate();
    
    // 저장 버튼 클릭 이벤트 처리
    saveButton.addEventListener('click', function() {
      const date = diaryDate.value;
      const content = diaryContent.value;
  
      if (date && content) {
        const newDiary = { date, content };
        diaries.push(newDiary);
        localStorage.setItem('diaries', JSON.stringify(diaries));
        diaryContent.value = ''; // 입력 필드 초기화
      } else {
        alert('날짜와 내용을 모두 입력해주세요.');
      }
    });
 });

    
// 모달 열기
    function modal(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.style.display = 'block';
        }
    }

// 모달 닫기
    const modalCloseButtons = document.querySelectorAll('.modal-close');
    modalCloseButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const modal = e.target.closest('.dialog');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });

/*
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
  */