(function() {


    var width = 320;
    var height = 0;
    var streaming = false;
    var video = null;
    var canvas = null;
    var photo = null;
    var startbutton1 = null;
    var constraints = {
      video: {
          width: { ideal: 4096 },
          height: { ideal: 2160 },
          facingMode: {
                exact: 'environment'
          }
      },
      audio: false,
    };
    function startup() {
      video = document.getElementById('video');
      canvas = document.getElementById('canvas');
      photo = document.getElementById('photo');
      startbutton1 = document.getElementById('startbutton1');

      navigator.mediaDevices.getUserMedia(constraints)
      .then(function(stream) {
        video.srcObject = stream;
        video.play();
      })

      .catch(function(err) {
        console.log("An error occurred: " + err);
      });

      video.addEventListener('canplay', function(ev){
        if (!streaming) {
          height = video.videoHeight / (video.videoWidth/width);


          if (isNaN(height)) {
            height = width / (4/3);
          }

          video.setAttribute('width', width);
          video.setAttribute('height', height);
          canvas.setAttribute('width', width);
          canvas.setAttribute('height', height);
          drawcanvas();
          streaming = true;
        }
      }, false);

      startbutton1.addEventListener('click', function(ev){
        takepicture();
        ev.preventDefault();
      }, false);

    }

    function clearphoto() {
      var context = canvas.getContext('2d');
      context.fillStyle = "#AAA";
      context.fillRect(0, 0, canvas.width, canvas.height);

      var data = canvas.toDataURL('image/png');
      photo.setAttribute('value', data);
    }

    function drawcanvas() {
      var context = canvas.getContext('2d');
      var centerX = canvas.width / 2;
      var centerY = canvas.height / 2;

      // Draw border of canvas
      context.lineWidth = "3";
      context.strokeStyle = "black";
      context.rect(0, 0, canvas.width, canvas.height);
      context.stroke();

      // Load in text
      context.textAlign = "center";
      context.font = "15px Arial";
      context.fillText("Screen capture will appear in this box", centerX, centerY);
    }

    function rotate90degrees() {
      var context = canvas.getContext('2d');
      context.translate(canvas.width, 0);
      context.rotate(Math.PI / 2);
    }

    function takepicture() {
      var context = canvas.getContext('2d');
      if (width && height) {
        canvas.width = width;
        canvas.height = height;
        context.drawImage(video, 0, 0, width, height);

        var data = canvas.toDataURL('image/png');
        photo.setAttribute('value', data);
        console.log(data)
      } else {
        clearphoto();
      }
    }
    window.addEventListener('load', startup, false);
  })();