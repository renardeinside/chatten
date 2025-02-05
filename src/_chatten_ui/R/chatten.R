# AUTO GENERATED FILE - DO NOT EDIT

#' @export
chatten <- function(id=NULL) {
    
    props <- list(id=id)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'Chatten',
        namespace = 'chatten_ui',
        propNames = c('id'),
        package = 'chattenUi'
        )

    structure(component, class = c('dash_component', 'list'))
}
