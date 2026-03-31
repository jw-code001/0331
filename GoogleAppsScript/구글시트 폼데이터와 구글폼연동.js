// 1. 시트를 열 때 사용자 맞춤 메뉴를 상단에 추가하는 함수
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('📝 설문조사 관리') // 생성될 메뉴 이름
      .addItem('구글 폼 업데이트하기 (동기화)', 'updateGoogleForm') // 클릭 시 실행될 함수
      .addToUi();
}

// 2. 시트 내용으로 구글 폼을 덮어씌우는 메인 함수
function updateGoogleForm() {
  var ui = SpreadsheetApp.getUi();
  
  // 🔥 주의: 여기에 동기화할 구글 폼의 ID를 넣어야 합니다!
  // 구글 폼 편집 화면 URL에서 /d/ 와 /edit 사이의 긴 문자열이 폼 ID입니다.
  var FORM_ID = '1iEnFV8pk3ZdXcn6-393m8urRZq75Apk_BeZL5bdE0g0'; 
  
 try {
    var form = FormApp.openById(FORM_ID);
  } catch(e) {
    ui.alert('폼을 찾을 수 없습니다. 코드 안의 FORM_ID를 다시 확인해주세요.');
    return;
  }
  
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('질문관리');
  var data = sheet.getDataRange().getValues();
  
  // 기존 폼에 있던 문항들 싹 지우기 (초기화)
  var items = form.getItems();
  for (var i = 0; i < items.length; i++) {
    form.deleteItem(items[i]);
  }
  
  // 시트 데이터를 읽어서 최신 문항으로 다시 채우기
  for (var i = 1; i < data.length; i++) {
    var qNum = data[i][0];
    var qText = data[i][1];
    var qType = data[i][2];
    var qOptionsStr = data[i][3];
    
    if (!qText) continue;
    
    var options = [];
    if (qOptionsStr) {
      // 쉼표로 자르고 -> 양옆 공백 없애고 -> 빈칸과 중복값 알아서 걸러내기
      options = qOptionsStr.toString().split(',')
        .map(function(item) { return item.trim(); })
        .filter(function(item, index, self) {
          return item !== "" && self.indexOf(item) === index;
        });
    }
    
    var fullTitle = "Q" + qNum + ". " + qText;
    
    // 옵션이 필요한 질문인데 옵션이 하나도 안 남았다면 건너뛰거나 에러 방지
    if ((qType === 'radio' || qType === 'checkbox') && options.length === 0) {
      options = ['선택지 없음 (시트 확인 필요)']; 
    }
    
    if (qType === 'radio') {
      form.addMultipleChoiceItem().setTitle(fullTitle).setChoiceValues(options);
    } else if (qType === 'checkbox') {
      form.addCheckboxItem().setTitle(fullTitle).setChoiceValues(options);
    } else if (qType === 'text') {
      form.addParagraphTextItem().setTitle(fullTitle);
    }
  }
  
  ui.alert('✅ 성공! 중복값을 자동으로 처리하여 구글 폼에 완벽하게 업데이트 되었습니다.');
}