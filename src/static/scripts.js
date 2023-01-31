// $.ajax({
//     url: "/chat/",
//     type: "POST",
//     dataType: "json",
//     success: function (response) {
//         console.log(response);
//     }
// });

function courseOptions() {
  let options = {
    'Fundies': {
      'Block': [1, 2, 3, 4],
      'Unit': [1, 2, 3]
    },
    'Test': {
      'Block': [1],
      'Unit': [1]
    }
  };

  $(document).ready(function() {
    let courseSelect = $('#course');
    let blockSelect = $('#block');
    let unitSelect = $('#unit');

    let savedCourse = localStorage.getItem("selectedCourse");
    let savedBlock = localStorage.getItem("selectedBlock");
    let savedUnit = localStorage.getItem("selectedUnit");

    if (savedCourse) {
      courseSelect.val(savedCourse);
      let blocks = options[savedCourse].Block;
      let units = options[savedCourse].Unit;

      blockSelect.empty();
      unitSelect.empty();

      for (let block of blocks) {
        let option = $('<option>', {
          value: block,
          text: block
        });
        blockSelect.append(option);
      }

      for (let unit of units) {
        let option = $('<option>', {
          value: unit,
          text: unit
        });
        unitSelect.append(option);
      }

      blockSelect.val(savedBlock);
      unitSelect.val(savedUnit);
    }

    courseSelect.change(function() {
      selectedCourse = $(this).val();
      let blocks = options[selectedCourse].Block;
      let units = options[selectedCourse].Unit;

      blockSelect.empty();
      unitSelect.empty();

      for (let block of blocks) {
        let option = $('<option>', {
          value: block,
          text: block
        });
        blockSelect.append(option);
      }

      for (let unit of units) {
        let option = $('<option>', {
          value: unit,
          text: unit
        });
        unitSelect.append(option);
      }

      localStorage.setItem("selectedCourse", selectedCourse);
    });

    blockSelect.change(function() {
      selectedBlock = $(this).val();
      localStorage.setItem("selectedBlock", selectedBlock);
    });

    unitSelect.change(function() {
      selectedUnit = $(this).val();
      localStorage.setItem("selectedUnit", selectedUnit);
    });
  });
}