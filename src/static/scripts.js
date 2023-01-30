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
      
        courseSelect.change(function() {
          selectedCourse = $(this).val();
          console.log("selected course: " + selectedCourse)
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
        });
    });
}
