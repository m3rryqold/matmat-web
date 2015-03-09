app.directive("counterwizard", function($timeout){
    return {
        restrict: "E",
        scope: {
            progress: "="
        },
        templateUrl: template_urls["counter-wizard"],
        controller: function($scope){
            var counter = $("#counter");
            $scope.$watch("progress", function(n, o){
                for (var i=0; i < n.length; i++){
                    if (n[i] != o[i]){
                        counter.find("div:nth-child("+(i+1)+") div").css("z-index", 1000+i);
                        div = counter.find("div:nth-child("+(i+1)+")");
                        div.addClass("animated");
                        $timeout(function(){
                            div.removeClass("animated");
                        }, 500);
                    }
                }
            }, true);
        }
    }
});