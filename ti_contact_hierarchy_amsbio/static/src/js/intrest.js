odoo.define('ti_website_crm_event_amsbio.onchange_intrest', function (require) {
    'use strict';

    $(document).ready(function() {
        var sub_intrest_required = false;
        $("input.intrest_tag").change(function() {
            var parent_tag_id = this.value
            if ($(this).prop('checked') == true){
                // $("#sub_tag_parent_id_" + parent_tag_id).removeClass("d-none");
                $("[data-parent_id='" + parent_tag_id + "']").removeClass("d-none");
                
                $(".intrest_warning_msg").hide();
                // $("#intrest_radio").attr("checked", true);
                
                // if( $("#sub_tag_parent_id_" + parent_tag_id).length > 0 || $(".sub_intrest_tag").is(":visible")){
                if( $("[data-parent_id='" + parent_tag_id + "']").length > 0 || $(".sub_intrest_tag").is(":visible")){
                    $(".sub_intrest_div").removeClass("d-none");
                    // $("#sub_intrest_radio").attr("required", true);
                    sub_intrest_required = true;

                }
                else{
                    $(".sub_intrest_div").addClass("d-none");
                    sub_intrest_required = false;
                }
            }
            else{
                // $("[data-parent_id='" + parent_tag_id + "']");
                
                // $("#sub_tag_parent_id_" + parent_tag_id).addClass("d-none");
                $("[data-parent_id='" + parent_tag_id + "']").addClass("d-none");
                
                console.log("\n", "#sub_tag_parent_id_" + parent_tag_id)
                // $("#sub_tag_parent_id_" + parent_tag_id + " .sub_intrest_tag").prop('checked', false);
                $("[data-parent_id='" + parent_tag_id + "']" + ".sub_intrest_tag").prop('checked', false);
                
                if (! $(".sub_intrest_tag").is(":visible")){
                    $(".sub_intrest_div").addClass("d-none");
                    // $("#sub_intrest_radio").attr("required", false);
                    sub_intrest_required = false;
                }
            }
        });


        $("input.sub_intrest_tag").change(function() {
            var parent_tag_id = $(this).attr("parent_tag_id")
            console.log($("[parent_tag_id=" + parent_tag_id + "]:checked"));

            if ($(this).prop('checked') == true){
                $(".sub_intrest_warning_msg").hide();
            }

            // Start: Code to add color to parent tag
            if($("[parent_tag_id=" + parent_tag_id + "]:checked").length > 0){
                $("label[for=tag_id_" + parent_tag_id + "]").addClass("text-success")
            }
            else{
                $("label[for=tag_id_" + parent_tag_id + "]").removeClass("text-success")
            }
            //End
        });

        $("#ti_new_lead_form").submit(function(ev){
            ev.preventDefault();
            // alert($("input.intrest_tag"));
            if($(".intrest_div input:checkbox:checked").length == 0){
                // alert("Selct Intrest");
                $(".intrest_warning_msg").show();
                return false
            }
            if ($(".sub_intrest_tag").is(":visible") && $(".sub_intrest_div input:checkbox:checked").length == 0){
                $(".sub_intrest_warning_msg").show();
                return false
            }
            this.submit();
          })

    });

});